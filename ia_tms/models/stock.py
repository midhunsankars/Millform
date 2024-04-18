# -*- coding: utf-8 -*-

from odoo import fields, models


class MoveLines(models.Model):
    _inherit = 'stock.move'

    load_id = fields.Many2one('tms.loads', 'Load ID')
    allocation_status = fields.Selection([('unallocated', 'Unallocated'),
                                          ('allocated', 'Allocated')],
                                         string='Allocation Status', default='unallocated')


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    slitter_warehouse = fields.Boolean('Slitter Warehouse')
