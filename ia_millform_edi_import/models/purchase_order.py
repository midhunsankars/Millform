# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_slit_order = fields.Boolean(default=False)

    @api.onchange('picking_type_id')
    def _onchange_picking_type_id(self):
        if self.picking_type_id:
            self.order_line.mapped('slit_id').action_reset()

    def button_cancel(self):
        result = super(PurchaseOrder, self).button_cancel()
        self.mapped('order_line.slit_id').action_reset()
        return result

    def button_approve(self, force=False):
        result = super(PurchaseOrder, self).button_approve(force=force)
        self.mapped('order_line.slit_id').action_done()
        return result


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    slit_id = fields.Many2one('edi.slitting.order', string='Slit', ondelete='cascade', copy=False)

    def action_view_slit_order(self):
        warehouse = self.order_id.picking_type_id.warehouse_id
        if not self.slit_id:
            location = self.order_id.picking_type_id.default_location_dest_id.id
            slit_order = self.env['edi.slitting.order'].create({
                'warehouse_id': warehouse and warehouse.id or False,
                'location_id': location or False,
                'purchase_line_id': self.id,
            })
            self.slit_id = slit_order.id
        else:
            if self.order_id.state in ['draft'] and self.slit_id.warehouse_id != warehouse:
                location = self.order_id.picking_type_id.default_location_dest_id.id
                self.slit_id.write({
                    'warehouse_id': warehouse and warehouse.id or False,
                    'location_id': location or False,
                    'quant_ids': [[5, 0, 0]],
                })

        view_id = self.env.ref('ia_millform_edi_import.edi_slitting_order_view_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Slit Order'),
            'view_mode': 'form',
            'res_model': 'edi.slitting.order',
            'target': 'new',
            'res_id': self.slit_id.id,
            'views': [[view_id, 'form']],
        }
