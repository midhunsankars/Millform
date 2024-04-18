# -*- coding: utf-8 -*-
import logging
import json
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_round, float_is_zero
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger("EDI Product Slit")


class EdiProductSlit(models.Model):
    _name = 'edi.product.slit'
    _description = 'Edi Product Slit'

    name = fields.Char(default='/')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('done', 'Done'),
        ],
        string='Status',
        required=True,
        readonly=True,
        copy=False,
        default='draft',
    )
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company)
    lines = fields.One2many('edi.product.slit.line', 'slit_id', string='Product Slit Lines', copy=False)

    # IMPORT FIELDS
    import_id = fields.Many2one('edi.import.slitlist', string='Import', required=False, ondelete='cascade', copy=False)
    master_coil = fields.Char(string='Master Coil')
    is_no_header = fields.Boolean(related='import_id.is_no_header')

    # IMPORT No Header FIELDS
    internal_ref = fields.Char(string='Internal Reference')
    supplier_bulk_product_code = fields.Char(string='Supplier Bulk Product Code')

    # COMMON FIELDS
    consumed_product_id = fields.Many2one('product.product', string='Consumed Product')
    order_id = fields.Many2one('purchase.order', string='Related PO')
    move_line_id = fields.Many2one('stock.move.line', string='Related Move Line')
    quantity = fields.Float('Done', related='move_line_id.quantity', store=True)
    lot_id = fields.Many2one('stock.lot', string='Related LOT')
    picking_id = fields.Many2one('stock.picking', string='Related Picking')
    total_qty = fields.Float(string='Total Qty', compute='_compute_total_qty', digits='Product Unit of Measure')
    total_margin = fields.Float(string='Waste %', compute='_compute_total_qty')

    # New fields
    bulk_sn = fields.Char(string='Bulk SerialNumber')
    queue_line_id = fields.Many2one('edi.slit.coil.order.queue.line', string='Order Line Queue', required=False,
                                    ondelete='cascade', copy=False)
    type = fields.Selection([('queue_import', 'Queue Import'), ('file_import', 'File Import')], string="Operation",
                            default='queue_import')
    slit_order_id = fields.Many2one(comodel_name='edi.slitting.order', string='Slit Order')
    slit_lines = fields.One2many(related='slit_order_id.lines')

    @api.model_create_multi
    def create(self, values):
        values['name'] = self.env['ir.sequence'].next_by_code('edi.product.slit')
        return super(EdiProductSlit, self).create(values)

    @api.depends('lines', 'quantity')
    def _compute_total_qty(self):
        for slit in self:
            total_qty = sum(slit.mapped('lines').mapped('coil_weight'))
            slit.total_margin = round(
                ((slit.quantity - total_qty) / slit.quantity) * 100, 2) if slit.quantity else 0
            slit.total_qty = total_qty

    def create_edi_log_line(self, message, queue_line, log_book):
        common_log_line_obj = self.env["common.log.lines.edi"]
        common_log_line_obj.edi_create_slit_log_line(message, log_book.model_id.id, queue_line, log_book)
        if queue_line:
            queue_line.write({"state": "failed", "processed_at": datetime.now()})

    def import_edi_orders_from_queue(self, order_data_lines, log_book):
        commit_count = 0
        for order_data_line in order_data_lines:
            if commit_count == 5:
                self._cr.commit()
                commit_count = 0
            commit_count += 1
            order_data = order_data_line.order_data
            order_response = json.loads(order_data)
            matching_po = False
            slit_lines = []
            if not order_response:
                continue
            lot_number = order_response[0].get('Bulk_SerialNumber', '')
            move_line = self.env['stock.move.line'].search(
                [('lot_name', '=', lot_number), ('state', '=', 'done'), ('picking_code', '=', 'incoming')], limit=1)
            if not move_line:
                lot_id = self.env['stock.lot'].search([('name', '=', lot_number)], limit=1)
                if lot_id:
                    move_line = self.env['stock.move.line'].search(
                        [('lot_id', '=', lot_id.id), ('state', '=', 'done'), ('picking_code', '=', 'incoming')],
                        limit=1)
                if not move_line:
                    message = 'No Stock Move found for (%s)' % lot_number
                    _logger.info(message)
                    self.create_edi_log_line(message, order_data_line, log_book)
                    continue
            for value in order_response:
                try:
                    po_number = value.get('OrderNo', '').strip()
                    matching_po = self.env['purchase.order'].search([('name', '=', po_number)], limit=1)
                    product_code = value.get('VendorProductCode', '').strip()
                    matching_suplierinfo = self.env['product.supplierinfo'].search(
                        [('product_code', '=', product_code)], limit=1)
                    if not matching_suplierinfo:
                        message = 'No Matching Vendor Pricelist found for (%s) Code' % product_code
                        _logger.info(message)
                        self.create_edi_log_line(message, order_data_line, log_book)
                        continue
                    product_id = matching_suplierinfo.product_id or matching_suplierinfo.product_tmpl_id.product_variant_ids[
                                                                    :1]
                    product_id = product_id.filtered(lambda p: p.type == 'product')
                    if not product_id:
                        message = 'No Product Assigned for Vendor Pricelist (%s)' % product_code
                        _logger.info(message)
                        self.create_edi_log_line(message, order_data_line, log_book)
                        continue
                    rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                    coil_weight = value.get('CoilWeight', '0')
                    product_quantity = coil_weight
                    product_quantity = product_id.uom_id._compute_quantity(
                        float(product_quantity),
                        move_line.product_uom_id,
                        rounding_method='HALF-UP')
                    product_quantity = float_round(product_quantity, precision_digits=rounding)
                    if float_is_zero(product_quantity, precision_digits=rounding):
                        message = 'No Quantity found in csv (%s)' % str(lot_number)
                        _logger.info(message)
                        self.create_edi_log_line(message, order_data_line, log_book)
                        continue
                    slit_lines.append((0, 0, {
                        'po_number': po_number,
                        'coil_weight': coil_weight,
                        'slit_sn': value.get('Slit_SerialNumber', '').strip(),
                        'vendor_product_code': product_code,
                        'finish_product_id': product_id.id,
                    }))
                except Exception as error:
                    if order_data_line:
                        order_data_line.write({"state": "failed", "processed_at": datetime.now()})
            if slit_lines:
                self.create({
                    'queue_line_id': order_data_line.id,
                    'consumed_product_id': move_line.product_id.id if move_line.product_id else False,
                    'order_id': matching_po and matching_po.id or False,
                    'move_line_id': move_line.id,
                    'lot_id': move_line.lot_id.id if move_line.lot_id else False,
                    'bulk_sn': lot_number,
                    'lines': slit_lines,
                })
                order_data_line.write({"state": "done", "processed_at": datetime.now()})

    def action_process_slit(self):
        self.ensure_one()
        if not self.move_line_id:
            raise ValidationError(_('No Stock Move found'))
        warehouse_id = self.move_line_id.move_id.warehouse_id or self.move_line_id.move_id.picking_id.picking_type_id.warehouse_id
        edi_config = self.env['edi.import.config'].search(
            [('type', '=', 'slit'), ('company_id', '=', self.company_id.id), ('warehouse_id', '=', warehouse_id.id)],
            limit=1)
        if not edi_config:
            raise ValidationError(_('No EDI Configuration found for SLIT'))
        rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        picking = self.env['stock.picking'].create({
            'picking_type_id': edi_config.pick_type_id.id,
            'location_id': edi_config.pick_type_id.default_location_src_id.id,
            'location_dest_id': edi_config.pick_type_id.default_location_dest_id.id,
        })
        self.picking_id = picking.id
        for line in self.lines:
            product_quantity = line.coil_weight
            product_quantity = line.finish_product_id.uom_id._compute_quantity(
                float(product_quantity),
                self.move_line_id.product_uom_id,
                rounding_method='HALF-UP')
            product_quantity = float_round(product_quantity, precision_digits=rounding)
            if float_is_zero(product_quantity, precision_digits=rounding):
                error_msg = str(line.vendor_product_code)
                raise ValidationError(_('No Quantity found in (%s)', error_msg))
            move_vals = {
                'product_uom_qty': product_quantity,
                'picking_id': picking.id,
                'slit_line_id': line.id,
            }
            finish_move_line = dict(
                move_vals,
                name=line.finish_product_id.name,
                product_id=line.finish_product_id.id,
                product_uom=line.finish_product_id.uom_id.id,
                location_id=picking.location_id.id,
                location_dest_id=picking.location_dest_id.id,
            )
            consumed_move_line = dict(
                move_vals,
                name=self.consumed_product_id.name,
                product_id=self.consumed_product_id.id,
                product_uom=self.consumed_product_id.uom_id.id,
                location_id=picking.location_dest_id.id,
                location_dest_id=picking.location_id.id,
            )
            self.env['stock.move'].create([finish_move_line, consumed_move_line])
        picking.action_confirm()
        for line in self.lines:
            if not line.move_ids:
                continue
            consumed_move_id = line.move_ids.filtered(lambda m: m.product_id == self.move_line_id.product_id)[:1]
            finish_move_id = (line.move_ids - consumed_move_id)[:1]
            if not finish_move_id.move_line_ids:
                move_line_vals = finish_move_id._prepare_move_line_vals(quantity=0)
                move_line_vals['lot_name'] = line.slit_sn
                move_line_vals['quantity'] = finish_move_id.product_uom_qty
                self.env['stock.move.line'].create(move_line_vals)
            else:
                finish_move_id.move_line_ids[:1].lot_name = line.slit_sn
                finish_move_id.move_line_ids[:1].quantity = finish_move_id.product_uom_qty
            if not consumed_move_id.move_line_ids:
                move_line_vals = consumed_move_id._prepare_move_line_vals(quantity=0)
                move_line_vals['lot_id'] = self.move_line_id.lot_id.id
                move_line_vals['quantity'] = consumed_move_id.product_uom_qty
                self.env['stock.move.line'].create(move_line_vals)
            else:
                consumed_move_id.move_line_ids[:1].lot_id = self.move_line_id.lot_id.id
                consumed_move_id.move_line_ids[:1].quantity = consumed_move_id.product_uom_qty
        picking.action_assign()
        action = picking.button_validate()
        self.write({'state': 'done'})
        if isinstance(action, dict):
            wizard = self.env[(action.get('res_model'))].browse(action.get('res_id')).with_context(
                action['context'])
            wizard.process()

    def action_view_picking(self):
        self.ensure_one()
        if self.picking_id:
            result = self.env['ir.actions.act_window']._for_xml_id('stock.stock_picking_action_picking_type')
            res = self.env.ref('stock.view_picking_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = self.picking_id.id
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result


class EdiProductSlitLine(models.Model):
    _name = 'edi.product.slit.line'
    _description = 'Edi Product Slit Line'

    slit_id = fields.Many2one('edi.product.slit', string='Slit', required=True, ondelete='cascade', copy=False)
    finish_product_id = fields.Many2one('product.product', string='Finished Product')
    lot_id = fields.Many2one('stock.lot', string='Related LOT')
    move_ids = fields.One2many('stock.move', 'slit_line_id', string='Stock Moves')

    # EDI Fields
    batch_id = fields.Char(string='Batch ID')
    product_code = fields.Char(string='Product Code')

    # EDI No Header Fields
    supplier_slit_product_code = fields.Char(string='Supplier Slit Product Code')
    output_qty = fields.Float(string='Output Qty', digits='Product Unit of Measure')

    po_number = fields.Char(string='PO Number')
    slit_sn = fields.Char(string='Slit SerialNumber')
    vendor_product_code = fields.Char(string='Vendor Product Code')
    coil_weight = fields.Float(string='Coil Weight', digits='Product Unit of Measure')
    process_charge = fields.Float(string='Process Charge')
