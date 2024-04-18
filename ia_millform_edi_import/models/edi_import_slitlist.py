# -*- coding: utf-8 -*-
import base64
import io
import os
from odoo import api, fields, Command, models, exceptions, _
from odoo.tools.float_utils import float_round, float_is_zero
from odoo.exceptions import UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')


class EdiImportSlitlist(models.Model):
    _name = 'edi.import.slitlist'
    _inherit = ["edi.import.base"]
    _description = 'Edi Import Slitlist'

    import_lines = fields.One2many('edi.import.slitlist.line', 'import_id', string='', copy=False)
    product_slit_lines = fields.One2many('edi.product.slit', 'import_id', string='', copy=False)
    is_no_header = fields.Boolean(string='No Header', default=False)

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
            if self.is_no_header:
                keys = ['internal_ref', 'supplier_bulk_product_code', 'slit_sn', 'supplier_slit_product_code',
                        'bulk_sn', 'output_qty']
            else:
                keys = ['po_number', 'master_coil', 'batch_id', 'product_code', 'coil_weight', 'process_charge']
            try:
                file_reader.extend(csv_reader)
            except Exception:
                raise exceptions.Warning(_("Invalid file...!"))

            for no in range(len(file_reader)):
                if no == 0 and not self.is_no_header:
                    continue
                try:
                    field = list(map(str, file_reader[no]))
                except ValueError:
                    raise exceptions.Warning(_("Dont Use Character only use numbers"))

                values = dict(zip(keys, field))
                if self.is_no_header:
                    if not values.get('bulk_sn', False):
                        raise ValidationError(_('No Bulk SN found in csv file - Line (%s)', str(no)))
                    if values['bulk_sn'] not in data_values:
                        data_values[values['bulk_sn']] = [values]
                    else:
                        data_values[values['bulk_sn']].append(values)
                else:
                    if not values.get('master_coil', False):
                        raise ValidationError(_('No Master Coil found in csv file - Line (%s)', str(no)))
                    if values['master_coil'] not in data_values:
                        data_values[values['master_coil']] = [values]
                    else:
                        data_values[values['master_coil']].append(values)
            for lot_number, values in data_values.items():
                move_line = self.env['stock.move.line'].search(
                    [('lot_name', '=', lot_number)], limit=1)
                if not move_line:
                    is_move = True
                    lot_id = self.env['stock.lot'].search([('name', '=', lot_number)], limit=1)
                    if not lot_id:
                        is_move = False
                    move_line = self.env['stock.move.line'].search([('lot_id', '=', lot_id.id)], limit=1)
                    if not move_line:
                        is_move = False
                    if not is_move:
                        raise ValidationError(_('No Stock Move found for (%s)', lot_number))
                po_number = ''
                internal_ref = ''
                supplier_bulk_product_code = ''
                matching_po = False
                slit_lines = []
                for value in values:
                    if not self.is_no_header:
                        po_number = value.get('po_number', '').strip()
                        matching_po = self.env['purchase.order'].search([('name', '=', po_number)], limit=1)
                        if not matching_po:
                            raise ValidationError(_('No Matching PO found for (%s)', str(po_number)))
                        if not value.get('master_coil', False):
                            raise ValidationError(_('No Master Coil found in csv file of (%s)', str(po_number)))
                        move_line_ids = matching_po.mapped('picking_ids').filtered(lambda p: p.state == 'done').mapped(
                            'move_ids').filtered(lambda m: m.state == 'done').mapped('move_line_ids')
                        if move_line not in move_line_ids:
                            raise ValidationError(
                                _('No stock move found for (%s) and (%s)', str(po_number), str(lot_number)))
                    if self.is_no_header:
                        internal_ref = value.get('internal_ref', '').strip()
                        supplier_bulk_product_code = value.get('supplier_bulk_product_code', '').strip()
                        product_code = value.get('supplier_slit_product_code', '').strip()
                    else:
                        product_code = value.get('product_code', '').strip()
                    matching_suplierinfo = self.env['product.supplierinfo'].search(
                        [('product_code', '=', product_code)], limit=1)
                    if not matching_suplierinfo:
                        raise ValidationError(_('No Matching Vendor Pricelist found for (%s) Code', product_code))
                    products = matching_suplierinfo.product_id or matching_suplierinfo.product_tmpl_id.product_variant_ids
                    if not products:
                        raise ValidationError(_('No Product Assigned for Vendor Pricelist (%s)', product_code))
                    product_id = products[0]
                    if product_id.type == 'product':
                        rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                        coil_weight = value.get('coil_weight', '0')
                        output_qty = value.get('output_qty', '0')
                        product_quantity = output_qty if self.is_no_header else coil_weight
                        product_quantity = product_id.uom_id._compute_quantity(
                            float(product_quantity),
                            move_line.product_uom_id,
                            rounding_method='HALF-UP')
                        product_quantity = float_round(product_quantity, precision_digits=rounding)
                        if float_is_zero(product_quantity, precision_digits=rounding):
                            raise ValidationError(_('No Quantity found in csv (%s)', str(po_number)))
                        slit_lines.append((0, 0, {
                            'po_number': po_number,
                            'coil_weight': output_qty if self.is_no_header else coil_weight,
                            'slit_sn': value.get('slit_sn', '').strip() if self.is_no_header else value.get('batch_id', '').strip(),
                            'vendor_product_code': product_code,
                            'finish_product_id': product_id.id,
                        }))
                        self.env['edi.import.slitlist.line'].create({
                            **value,
                            'import_id': self.id,
                            'product_id': product_id.id,
                            'order_id': matching_po and matching_po.id or False,
                        })
                if slit_lines:
                    slit_orders = self.env['edi.slitting.order']
                    self.write({'state': 'imported'})
                    if move_line.lot_id:
                        slit_orders = slit_orders.search([('quant_ids.lot_id', '=', move_line.lot_id.id)])[:1]

                    self.env['edi.product.slit'].create({
                        'import_id': self.id,
                        'consumed_product_id': move_line.product_id.id if move_line.product_id else False,
                        'order_id': matching_po and matching_po.id or False,
                        'move_line_id': move_line.id,
                        'lot_id': move_line.lot_id.id if move_line.lot_id else False,
                        'bulk_sn': lot_number,
                        'lines': slit_lines,
                        'type': 'file_import',
                        'slit_order_id': slit_orders.id if slit_orders else False,
                    })

    def action_view_slit(self):
        self.ensure_one()
        result = self.env['ir.actions.act_window']._for_xml_id('ia_millform_edi_import.edi_product_slit_view_action')
        if len(self.product_slit_lines) > 1:
            result['domain'] = [('id', 'in', self.product_slit_lines.ids)]
        elif len(self.product_slit_lines) == 1:
            res = self.env.ref('ia_millform_edi_import.edi_product_slit_view_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = self.product_slit_lines.id
        else:
            result = {'type': 'ir.actions.act_window_close'}

        return result


class EdiImportSlitlistLine(models.Model):
    _name = 'edi.import.slitlist.line'
    _description = 'Edi Import Slitlist Line'

    import_id = fields.Many2one('edi.import.slitlist', string='Import', required=True, ondelete='cascade', copy=False)
    po_number = fields.Char(string='PO Number')
    master_coil = fields.Char(string='Master Coil')
    batch_id = fields.Char(string='Batch ID')
    product_code = fields.Char(string='Product Code')
    coil_weight = fields.Float(string='Coil Weight', digits='Product Unit of Measure')
    process_charge = fields.Float(string='Process Charge')
    product_id = fields.Many2one('product.product', string='Product')
    order_id = fields.Many2one('purchase.order', string='PO')
    picking_id = fields.Many2one('stock.picking', string='Picking')

    # No Header Fields
    internal_ref = fields.Char(string='Internal Reference')
    supplier_bulk_product_code = fields.Char(string='Supplier Bulk Product Code')
    bulk_sn = fields.Char(string='Bulk SN')
    supplier_slit_product_code = fields.Char(string='Supplier Slit Product Code')
    slit_sn = fields.Char(string='Slit SN')
    output_qty = fields.Float(string='Output Qty', digits='Product Unit of Measure')
