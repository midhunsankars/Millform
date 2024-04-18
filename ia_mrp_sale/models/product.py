from odoo import api, fields, models, _


class ProductTemplates(models.Model):
    _inherit = 'product.template'

    workcenter_ids = fields.Many2many(
        'mrp.workcenter',
        'product_temp_mrp_center_rel',
        'prod_id',
        'mrp_center_id',
        string='Work Center')
    cartridge_no = fields.Char('Cartridge No')
    cartridge_setup_time = fields.Float('Cartridge Setup Time')
    profile_setup_time = fields.Float('Profile Setup Time')
