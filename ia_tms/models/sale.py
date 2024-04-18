# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class SoLineBundles(models.Model):
    _inherit = 'so.line.bundles'

    @api.depends('sale_id.picking_ids', 'sale_id.picking_ids.state')
    def _compute_used(self):
        for record in self:
            record.internal_id = False
            record.outgoing_id = False
            if record.sale_id and record.sale_id.state in ('sale', 'done'):
                internal_id = record.sale_id.picking_ids.filtered(
                    lambda a: a.picking_type_id.code == 'internal' and a.state not in ('cancel'))
                record.internal_id = internal_id and internal_id[0].id or False
                outgoing_id = record.sale_id.picking_ids.filtered(
                    lambda a: a.picking_type_id.code == 'outgoing' and a.state not in ('cancel'))
                record.outgoing_id = outgoing_id and outgoing_id[0].id or False
                record.delivery_partner_id = outgoing_id and outgoing_id[0].partner_id.id or False
                record.warehouse_id = record.sale_id.warehouse_id.id
                record.location_id = internal_id and internal_id[0].location_id.id or False
                record.location_dest_id = internal_id and internal_id[0].location_dest_id.id or False

    sale_id = fields.Many2one(related="so_line_id.order_id", string="Sale order", readonly=True, store=True)
    internal_id = fields.Many2one('stock.picking', compute='_compute_used', string='Internal Picking', store=True)
    outgoing_id = fields.Many2one('stock.picking', compute='_compute_used', string='Delivery Picking', store=True)
    load_delivery_id = fields.Many2one('tms.loads', 'Delivery Load ID')
    load_internal_id = fields.Many2one('tms.loads', 'Internal Load ID')
    allocation_status = fields.Selection([('unallocated', 'Unallocated'),
                                          ('allocated', 'Allocated')],
                                         string='Allocation Status', default='unallocated')
    delivery_partner_id = fields.Many2one('res.partner', 'Delivery Address', compute='_compute_used', store=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', compute='_compute_used', store=True)
    location_id = fields.Many2one('stock.location', 'From', compute='_compute_used', store=True)
    location_dest_id = fields.Many2one('stock.location', 'To', compute='_compute_used', store=True)
