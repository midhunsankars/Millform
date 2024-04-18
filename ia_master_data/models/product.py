# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    qty_per_pack = fields.Float('Qty per Pack')
    std_pack_weight_limit = fields.Float('Std pack weight limit')
    std_step = fields.Float('Standard Step')
    jh_mini_pack_qty = fields.Float('JH Mini Pack Qty')
    can_be_punched = fields.Selection([("yes", "Yes"), ("no", "No")], string="Can be Punched")
    punch_markings = fields.Selection([("yes", "Yes"), ("no", "No")], string="Punch Markings")
    bridging_reduce_by = fields.Float('Bridging Recude by', digits=(16, 3))
    full_pack = fields.Selection([("yes", "Yes"), ("no", "No")], string="Full Pack")
    fixed_length = fields.Float('Fixed Length')
    coil_width = fields.Float('Width')
    coil_thickness = fields.Float('Thickness')
    upstream_stock_ids = fields.Many2many('product.product', 'upstream_product_product_rel',
                                          string='Upstream Stock Code')
    cover_sheet_available = fields.Selection([("yes", "Yes"), ("no", "No")], string="Cover Sheet available")
    weight = fields.Float(digits=(16, 6))
