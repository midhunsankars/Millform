# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AllocateLoads(models.TransientModel):
    _name = "tms.loads.allocate"
    _description = 'Allocate to Loads'

    load_id = fields.Many2one('tms.loads', 'Load')

    def action_allocate(self):
        stock_moves = self.env['stock.move'].browse(self._context.get('active_ids', []))
        for moves in stock_moves:
            moves.write({'load_id': self.load_id.id, 'allocation_status': 'allocated'})

            transfer_in_loads = self.load_id.mapped('load_line_ids.transfer_id').ids
            if moves.picking_id.id not in transfer_in_loads:
                trns_vals = {
                    'load_id': self.load_id.id,
                    'transfer_id': moves.picking_id.id,
                    'partner_id': moves.sale_line_id and moves.sale_line_id.order_id.partner_id.id or moves.partner_id.id,
                    'partner_latitude': moves.partner_id.partner_latitude,
                    'partner_longitude': moves.partner_id.partner_longitude,
                    'delivery_partner_id': moves.partner_id.id,
                }
                if moves.picking_code == 'incoming':
                    trns_vals['type'] = 'pickup'
                if moves.picking_code == 'outgoing':
                    trns_vals['type'] = 'delivery'
                if moves.picking_code == 'internal':
                    trns_vals['type'] = 'transfer'
                self.env['tms.loads.lines'].create(trns_vals)
        return True


class BundleAllocateLoads(models.TransientModel):
    _name = "bundle.loads.allocate"
    _description = 'Bundle Allocate to Loads'
    load_id = fields.Many2one('tms.loads', 'Load')

    def action_allocate(self):
        so_line_bundles = self.env['so.line.bundles'].browse(self._context.get('active_ids', []))
        sale_orders = so_line_bundles.mapped('so_line_id.order_id').sorted('id')
        for so in sale_orders:
            trns_vals = {
                'load_id': self.load_id.id,
                'partner_id': so.partner_id.id or False,
                'partner_latitude': so.partner_id.partner_latitude,
                'partner_longitude': so.partner_id.partner_longitude,
                'delivery_partner_id': so.picking_ids.mapped('partner_id').id,
                'transfer_id': so.picking_ids.mapped('id')[0],

            }
            line_bundles = so_line_bundles.filtered(lambda m: m.so_line_id.order_id.id == so.id)
            trns_vals['type'] = 'delivery'
            trns_vals['bundle_ids'] = line_bundles and line_bundles.ids or []
            self.env['tms.loads.lines'].create(trns_vals)
            if self._context.get('tran_type', False) == 'internal':
                line_bundles.write({'load_internal_id': self.load_id.id, 'allocation_status': 'allocated'})
            elif self._context.get('tran_type', False) == 'sale':
                line_bundles.write({'load_delivery_id': self.load_id.id, 'allocation_status': 'allocated'})
        return True
