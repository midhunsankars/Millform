# -*- coding: utf-8 -*-
import logging
import json
from datetime import datetime, timedelta

from odoo import api, fields, Command, models, exceptions, _
from odoo.tools.float_utils import float_round, float_is_zero
from odoo.exceptions import UserError, ValidationError

from itertools import groupby
from operator import itemgetter

_logger = logging.getLogger("BulkCoil Order Coil Line")


class EdiBulkCoilLine(models.Model):
    _name = 'edi.bulk.coil.line'
    _description = 'Edi Bulk Coil Line'

    sn_number = fields.Char(string='Batch ID')
    vendor_code = fields.Char(string='Product Description')
    qty_done = fields.Float(string='Coil Weight')
    received_date = fields.Char(string='Receipt Date')
    product_id = fields.Many2one('product.product', string='Product')
    order_id = fields.Many2one('purchase.order', string='PO',
                               domain="[('order_line.product_id', '=', product_id), ('state', '=', 'purchase')]")
    queue_line_id = fields.Many2one('edi.bulk.coil.order.queue.line', string='Order Line Queue', required=False,
                                    ondelete='cascade', copy=False)
    state = fields.Selection([('draft', 'Draft'), ('completed', 'Completed'), ('failed', 'Failed')], default='draft')
    active = fields.Boolean('Active', default=True)
    type = fields.Selection([('queue_import', 'Queue Import'), ('file_import', 'File Import')], string="Operation",
                            default='queue_import')

    def create_edi_log_line(self, message, queue_line, log_book):
        common_log_line_obj = self.env["common.log.lines.edi"]

        common_log_line_obj.edi_create_bulk_log_line(message, log_book.model_id.id, queue_line, log_book)
        if queue_line:
            queue_line.write({"state": "failed", "processed_at": datetime.now()})

    def import_edi_orders(self, order_data_lines, log_book):
        commit_count = 0
        for order_data_line in order_data_lines:
            if commit_count == 5:
                self._cr.commit()
                commit_count = 0
            commit_count += 1
            order_data = order_data_line.order_data
            order_response = json.loads(order_data)

            matching_suplierinfo = self.env['product.supplierinfo'].search(
                [('product_code', '=', order_response.get('ProductDescription'))], limit=1)
            if not matching_suplierinfo:
                message = 'No Matching Vendor Pricelist found for (%s) Code' % str(
                    order_response.get('ProductDescription'))
                _logger.info(message)
                self.create_edi_log_line(message, order_data_line, log_book)
                continue
            product = matching_suplierinfo.product_id or matching_suplierinfo.product_tmpl_id.product_variant_ids[:1]
            if not product:
                message = 'No Product Assigned for Vendor Pricelist (%s)' % str(
                    order_response.get('ProductDescription'))
                _logger.info(message)
                self.create_edi_log_line(message, order_data_line, log_book)
                continue

            self.create({
                'queue_line_id': order_data_line.id,
                'sn_number': order_response.get('BatchID', ''),
                'vendor_code': order_response.get('ProductDescription', ''),
                'qty_done': order_response.get('CoilWeight', ''),
                'received_date': order_response.get('RecieptDate', ''),
                'product_id': product and product.id or False,
                'type': 'queue_import',
            })
            order_data_line.write({"state": "done", "processed_at": datetime.now()})

    def action_process_bulk(self):
        lines_without_po = self.filtered(lambda b: not b.order_id)
        if lines_without_po:
            raise ValidationError(_('No Assigned for %(bulks)s', bulks=', '.join(lines_without_po.mapped('sn_number'))))
        lines_with_po = self.filtered('order_id')
        grouped_bulks = groupby(lines_with_po, itemgetter('order_id'))
        for order_id, values in grouped_bulks:
            po_to_validate = self.env['stock.picking']
            if order_id.state not in ('purchase', 'done'):
                raise ValidationError(_('Purchase (%s) not in Valid state', str(order_id.name)))
            pickings = order_id.mapped('picking_ids').filtered(
                lambda picking: picking.state not in ('cancel', 'done'))
            moves = pickings.mapped('move_ids').filtered(lambda m: m.state not in ('cancel', 'done'))
            edi_update_moves = []
            processed_moves = []
            validated_bulk_lines = self.env['edi.bulk.coil.line']
            for value in values:
                stock_lot = self.env['stock.lot'].search([('name', '=', value.sn_number)], limit=1)
                if stock_lot:
                    raise ValidationError(
                        _('Batch Id Already Created In System (%s), Use Different Lot Name', str(value.sn_number)))
                if not value.vendor_code:
                    raise ValidationError(_('No Vendor code found in csv file of (%s)', str(value.vendor_code)))
                matching_suplierinfo = self.env['product.supplierinfo'].search(
                    [('product_code', '=', value.vendor_code)], limit=1)
                if not matching_suplierinfo:
                    raise ValidationError(
                        _('No Matching Vendor Pricelist found for (%s) Code', str(value.vendor_code)))
                product_id = matching_suplierinfo.product_id or matching_suplierinfo.product_tmpl_id.product_variant_ids[:1]
                product_id = product_id.filtered(lambda p: p.type == 'product')
                if not product_id:
                    raise ValidationError(
                        _('No Product Assigned for Vendor Pricelist (%s)', str(value.vendor_code)))
                _logger.info("Matched Product (%s) Found For EDI Receipts Import", str(product_id.name))
                product_move = moves.filtered(lambda m: m.product_id == product_id and m.state not in ('cancel', 'done'))[:1]
                if not product_move:
                    raise ValidationError(_('No Matching Stock Move found for (%s) Product', str(product_id.name)))
                po_to_validate |= product_move.picking_id
                rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                uom_quantity = product_move.product_id.uom_id._compute_quantity(float(value.qty_done),
                                                                                product_move.product_uom,
                                                                                rounding_method='HALF-UP')
                uom_quantity = float_round(uom_quantity, precision_digits=rounding)
                move_lines_commands = []

                if product_move.move_line_ids and product_move not in processed_moves:
                    product_move.move_line_ids.unlink()
                move_line_vals = product_move._prepare_move_line_vals(quantity=0)
                if product_id.tracking != 'none':
                    move_line_vals['lot_name'] = value.sn_number
                move_line_vals['quantity'] = uom_quantity
                move_lines_commands.append((0, 0, move_line_vals))

                processed_moves.append(product_move)
                product_move.write({'move_line_ids': move_lines_commands})
                validated_bulk_lines |= value
            if po_to_validate:
                po_to_validate.action_assign()
                action = po_to_validate.button_validate()
                if isinstance(action, dict):
                    wizard = self.env[(action.get('res_model'))].browse(action.get('res_id')).with_context(
                        action['context'])
                    wizard.process()
                validated_bulk_lines.write({'state': 'completed'})
