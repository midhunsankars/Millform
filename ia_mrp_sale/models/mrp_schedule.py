# -*- coding: utf-8 -*-

from odoo import api, fields, models


class MrpSchedule(models.Model):
    _name = 'mrp.schedule'
    _order = "sequence, id"
    _description = 'Mrp Schedule'

    name = fields.Char(compute='_compute_name')
    sequence = fields.Integer(
        'Sequence', default=1, required=True,
        help="Gives the sequence order when displaying a list of production schedule.")
    schedule_type = fields.Selection([
        ('mrp', 'Mrp'),
        ('coil_change', 'Coil Change'),
        ('cartridge_change', 'Cartridge Change'),
        ('gauge_change', 'Gauge Change'),
        ('product_change', 'Product Change'),
    ], default='mrp', copy=False)
    production_id = fields.Many2one(comodel_name='mrp.production', string='Production')
    sale_id = fields.Many2one(related='production_id.sale_id')
    product_id = fields.Many2one(related='production_id.product_id')
    product_uom_id = fields.Many2one(related='production_id.product_uom_id')
    product_qty = fields.Float(related='production_id.product_qty')
    date_start = fields.Datetime(related='production_id.date_start')
    production_ready = fields.Boolean(related='production_id.production_ready')
    value = fields.Float(string='Value')
    workcenter_id = fields.Many2one('mrp.workcenter', 'Work Center', check_company=True)
    company_id = fields.Many2one(related='production_id.company_id')
    rel_production_ids = fields.Many2many(
        'mrp.production',
        'mrp_schedule_production_rel',
        'schedule_id',
        'production_id',
        string='Related Productions')

    @api.depends('schedule_type', 'production_id')
    def _compute_name(self):
        for rec in self:
            name = '/'
            if rec.production_id:
                name = rec.production_id.name
            elif rec.schedule_type:
                name = dict(self._fields['schedule_type'].selection).get(rec.schedule_type)
            rec.name = name

    def assign_costing(self):
        schedules = self.filtered(lambda s: s.schedule_type == 'mrp')
        self.create({
            'schedule_type': 'coil_change',
            'rel_production_ids': schedules.mapped('production_id').ids if schedules else []
        })
