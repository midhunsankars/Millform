# -*- coding: utf-8 -*-

##############################################################################
#    Copyright (C) Ioppolo and Associates (I&A) 2023 (<http://ioppolo.com.au>).
###############################################################################

from odoo import fields, models, api
from dateutil.relativedelta import relativedelta


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    source_procurement_group_id = fields.Many2one(
        comodel_name="procurement.group",
        readonly=True,
    )
    sale_id = fields.Many2one(
        comodel_name="sale.order",
        string="Sale order",
        readonly=True,
        store=True,
        related="source_procurement_group_id.sale_id",
    )
    sale_line_id = fields.Many2one('sale.order.line', string='Sales Order Item')
    sequence = fields.Integer('Sequence')
    production_ready = fields.Boolean('Ready for Production')

    def _assign_to_schedule(self):
        MrpSchedule = self.env['mrp.schedule']
        for production in self:
            is_assigned = MrpSchedule.search_count([('production_id', 'in', production.id)])
            if is_assigned:
                continue
            MrpSchedule.create({
                'schedule_type': 'mrp',
                'production_id': production.id,
            })


class WorkCenter(models.Model):
    _inherit = "mrp.workcenter"

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
