# -*- coding: utf-8 -*-
from odoo import api, fields, Command, models, exceptions, _

import logging

_logger = logging.getLogger(__name__)


class EdiSlitOrder(models.Model):
    _name = 'edi.slitting.order'
    _description = 'Edi Slitting Order'

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
    product_id = fields.Many2one('product.product', string='Product',
                                 domain=[('tracking', 'in', ['serial', 'lot'])])
    company_id = fields.Many2one(
        string="Company",
        comodel_name='res.company',
        default=lambda self: self.env.company,
        required=True,
    )
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True,
                                   domain="[('company_id', '=', company_id)]")
    location_id = fields.Many2one(
        string="Stock Location",
        comodel_name='stock.location',
        domain="[('usage', '=', 'internal'), ('company_id', '=', company_id)]",
        check_company=True,
        required=True,
    )
    lines = fields.One2many('edi.slitting.order.line', 'slit_id', string='Slitting Order Lines', copy=False)
    lot_lines = fields.One2many('edi.slitting.order.lot', 'slit_id', string='Slitting Order Lot Lines', copy=False)
    quant_ids = fields.Many2many(comodel_name='stock.quant', string='Serial Numbers')
    available_quant_ids = fields.Many2many(comodel_name='stock.quant', compute='_compute_available_quant_ids')
    purchase_line_id = fields.Many2one('purchase.order.line', 'Purchase Order Line', ondelete='set null')
    coil_width = fields.Float(related='product_id.coil_width')
    total_width = fields.Float(string='Total Width', compute='_compute_total_width')
    total_width_margin = fields.Float(string='Waste %', compute='_compute_total_width')
    total_available_qty = fields.Float(string='Total Available Qty', compute='_compute_total_available_qty', store=True)

    @api.depends('lines', 'product_id', 'coil_width')
    def _compute_total_width(self):
        for slit in self:
            if not slit.coil_width:
                total_width = 0
                total_width_margin = 0
            else:
                total_width = sum(slit.mapped('lines').mapped('coil_width'))
                total_width_margin = round(((slit.coil_width - total_width) / slit.coil_width) * 100,
                                           2) if slit.coil_width and total_width else 0
                slit.total_width = total_width
            slit.total_width = total_width
            slit.total_width_margin = total_width_margin

    @api.depends('product_id', 'location_id', 'product_id.qty_available')
    def _compute_available_quant_ids(self):
        for slit in self:
            if not slit.product_id or not slit.location_id:
                slit.available_quant_ids = []
            else:
                lot_quants = self.env['stock.quant']._gather(slit.product_id, slit.location_id)
                used_lots = self.env['edi.slitting.order'].search(
                    [('purchase_line_id', '!=', False), ('purchase_line_id', '!=', slit.id)]).mapped('quant_ids')
                slit.available_quant_ids = lot_quants - used_lots

    @api.depends('quant_ids')
    def _compute_total_available_qty(self):
        for slit in self:
            slit.total_available_qty = sum(slit.quant_ids.mapped('available_quantity'))

    def action_done(self):
        for slit in self:
            slit.write({
                'state': 'done',
            })

    def action_reset(self):
        for slit in self:
            slit.write({
                'state': 'draft',
                'quant_ids': [[5, 0, 0]],
                'lines': [[5, 0, 0]],
            })

    def write(self, vals):
        result = super(EdiSlitOrder, self).write(vals)
        if 'quant_ids' in vals:
            for slit in self:
                purchase_line_id = slit.purchase_line_id.filtered(lambda l: l.state not in ('done', 'cancel'))
                if purchase_line_id:
                    purchase_line_id.product_qty = slit.total_available_qty
        return result


class EdiSlitOrderLine(models.Model):
    _name = 'edi.slitting.order.line'
    _description = 'Edi Slitting Order Line'

    product_id = fields.Many2one('product.product', string='Product',
                                 domain=[('tracking', 'in', ['serial', 'lot'])])
    coil_width = fields.Float(related='product_id.coil_width')
    cut_size = fields.Char(string='Cut Size')
    brand_as = fields.Char(string='Brand As')
    slit_id = fields.Many2one('edi.slitting.order', string='Slit', required=True, ondelete='cascade', copy=False)


class EdiSlitOrderLot(models.Model):
    _name = 'edi.slitting.order.lot'
    _description = 'Edi Slitting Order Lot'

    lot_id = fields.Many2one(
        'stock.lot', 'Lot/Serial Number')
    quantity = fields.Float(
        'Quantity',
        readonly=True, digits='Product Unit of Measure')
    slit_id = fields.Many2one('edi.slitting.order', string='Slit', required=True, ondelete='cascade', copy=False)
