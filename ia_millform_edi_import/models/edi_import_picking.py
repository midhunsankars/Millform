# -*- coding: utf-8 -*-
import base64
import io
import os
from odoo import api, fields, Command, models, exceptions, _
from odoo.tools.float_utils import float_round
from odoo.exceptions import UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')


class EdiImportPicking(models.Model):
    _name = 'edi.import.picking'
    _inherit = ["edi.import.base"]
    _description = 'Edi Import Picking'

    import_lines = fields.One2many('edi.import.picking.line', 'import_id', string='', copy=True)

    def import_file_edi(self):
        # OVERRIDE
        super().import_file_edi()
        file_name = str(self.file_name)
        if self.import_file:
            if '.' not in file_name:
                raise ValidationError(_('Please upload valid xls or csv file.!'))
            name, extension = os.path.splitext(file_name)
            if extension != '.csv':
                raise ValidationError(_('Please upload csv file.!'))

            csv_data = base64.b64decode(self.import_file)
            data_file = io.StringIO(csv_data.decode("utf-8"))
            data_file.seek(0)
            file_reader = []
            csv_reader = csv.reader(data_file, delimiter=',')
            data_values = {}
            keys = ['sn_number', 'vendor_code', 'qty_done', 'received_date', 'po_number']
            try:
                file_reader.extend(csv_reader)
            except Exception:
                raise exceptions.Warning(_("Invalid file...!"))

            for no in range(len(file_reader)):
                if no != 0:
                    try:
                        field = list(map(str, file_reader[no]))
                    except ValueError:
                        raise exceptions.Warning(_("Dont Use Character only use numbers"))

                    values = dict(zip(keys, field))
                    if values['po_number'] not in data_values:
                        data_values[values['po_number']] = [values]
                    else:
                        data_values[values['po_number']].append(values)
            for po_number, values in data_values.items():
                po_to_validate = self.env['stock.picking']
                matching_pos = self.env['purchase.order'].search([('name', '=', po_number)], limit=1)
                if not matching_pos:
                    raise ValidationError(_('No Matching PO found for (%s)', str(po_number)))
                _logger.info("Matched PO (%s) Found For EDI Receipts Import", str(matching_pos.name))
                if matching_pos.state not in ('purchase', 'done'):
                    raise ValidationError(_('Purchase (%s) not in Valid state', str(po_number)))
                pickings = matching_pos.mapped('picking_ids').filtered(
                    lambda picking: picking.state not in ('cancel', 'done'))
                moves = pickings.mapped('move_ids').filtered(lambda m: m.state not in ('cancel', 'done'))
                edi_update_moves = []
                for value in values:
                    if not value.get('vendor_code', False):
                        raise ValidationError(_('No Vendor code found in csv file of (%s)', str(po_number)))
                    matching_suplierinfo = self.env['product.supplierinfo'].search(
                        [('product_code', '=', value.get('vendor_code'))], limit=1)
                    if not matching_suplierinfo:
                        raise ValidationError(_('No Matching Vendor Pricelist found for (%s) Code', str(value.get('vendor_code'))))
                    products = matching_suplierinfo.product_id or matching_suplierinfo.product_tmpl_id.product_variant_ids
                    if not products:
                        raise ValidationError(_('No Product Assigned for Vendor Pricelist (%s)', str(value.get('vendor_code'))))
                    if products and products[0].type == 'product':
                        _logger.info("Matched Product (%s) Found For EDI Receipts Import", str(products[0].name))
                        product_moves = moves.filtered(lambda m: m.product_id == products[0])
                        product_move = product_moves and product_moves[:1]
                        if not product_move:
                            raise ValidationError(_('No Matching Stock Move found for (%s) Product', str(products[0].name)))
                        po_to_validate |= product_move.picking_id
                        rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                        uom_quantity = product_move.product_id.uom_id._compute_quantity(float(value.get('qty_done', '0')),
                                                                                        product_move.product_uom,
                                                                                        rounding_method='HALF-UP')
                        uom_quantity = float_round(uom_quantity, precision_digits=rounding)
                        move_lines_commands = []
                        if products[0].tracking != 'none':
                            # TODO: check if lot already assigned to a line, Lot should be used once like SN
                            if not product_move.move_line_ids:
                                move_line_vals = product_move._prepare_move_line_vals(quantity=0)
                                move_line_vals['lot_name'] = value.get('sn_number', '')
                                move_line_vals['quantity'] = uom_quantity
                                move_line = self.env['stock.move.line'].create(move_line_vals)
                                edi_update_moves.append(move_line.id)
                            else:
                                if len(product_move.mapped('move_line_ids')) == 1:
                                    if product_move.move_line_ids.id in edi_update_moves:
                                        move_line_vals = product_move._prepare_move_line_vals(quantity=0)
                                        move_line_vals['lot_name'] = value.get('sn_number', '')
                                        move_line_vals['quantity'] = uom_quantity
                                        move_lines_commands.append((0, 0, move_line_vals))
                                    else:
                                        move_lines_commands.append(Command.update(product_move.move_line_ids.id, {
                                            'lot_name': value.get('sn_number', ''),
                                            'quantity': uom_quantity,
                                        }))
                                        edi_update_moves.append(product_move.move_line_ids.id)
                                else:
                                    move_line_vals = product_move._prepare_move_line_vals(quantity=0)
                                    move_line_vals['lot_name'] = value.get('sn_number', '')
                                    move_line_vals['quantity'] = uom_quantity
                                    move_lines_commands.append((0, 0, move_line_vals))
                        else:
                            if not product_move.move_line_ids:
                                move_line_vals = product_move._prepare_move_line_vals(quantity=0)
                                move_line_vals['quantity'] = uom_quantity
                                move_line = self.env['stock.move.line'].create(move_line_vals)
                                edi_update_moves.append(move_line.id)
                            else:
                                if len(product_move.mapped('move_line_ids')) == 1:
                                    if product_move.move_line_ids.id in edi_update_moves:
                                        move_line_vals = product_move._prepare_move_line_vals(quantity=0)
                                        move_line_vals['quantity'] = uom_quantity
                                        move_lines_commands.append((0, 0, move_line_vals))
                                    else:
                                        move_lines_commands.append(Command.update(product_move.move_line_ids.id, {
                                            'quantity': uom_quantity,
                                        }))
                                        edi_update_moves.append(product_move.move_line_ids.id)
                                else:
                                    move_line_vals = product_move._prepare_move_line_vals(quantity=0)
                                    move_line_vals['quantity'] = uom_quantity
                                    move_lines_commands.append((0, 0, move_line_vals))
                        product_move.write({'move_line_ids': move_lines_commands})
                        self.env['edi.import.picking.line'].create({
                            **value,
                            'import_id': self.id,
                            'product_id': products[0].id,
                            'order_id': matching_pos.id,
                        })
                if po_to_validate:
                    po_to_validate.action_assign()
                    action = po_to_validate.button_validate()
                    if isinstance(action, dict):
                        wizard = self.env[(action.get('res_model'))].browse(action.get('res_id')).with_context(
                            action['context'])
                        wizard.process()
                        self.write({'state': 'imported'})
                    else:
                        self.write({'state': 'imported'})


class EdiImportPickingLine(models.Model):
    _name = 'edi.import.picking.line'
    _description = 'Edi Import Picking Line'

    import_id = fields.Many2one('edi.import.picking', string='Import', required=True, ondelete='cascade', copy=False)
    sn_number = fields.Char(string='Coil Batchcode')
    vendor_code = fields.Char(string='Supplier Coil Stockcode')
    qty_done = fields.Float(string='Weight Tonnes')
    received_date = fields.Char(string='Receipt Date')
    po_number = fields.Char(string='Coil P/O')
    product_id = fields.Many2one('product.product', string='Product')
    order_id = fields.Many2one('purchase.order', string='PO')
