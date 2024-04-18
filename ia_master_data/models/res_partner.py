# -*- coding: utf-8 -*-

from odoo import fields, models


class PartnerArea(models.Model):
    _name = 'res.partner.area'
    _description = 'Partner Area'

    name = fields.Char('Area')
    nearest_warehouse_id = fields.Many2one('stock.warehouse', 'Nearest Warehouse')
    metro = fields.Boolean('Metro')


class Partner(models.Model):
    _inherit = 'res.partner'

    loading_notes = fields.Char('Loading Notes')
    max_bundle_weight_limit = fields.Float('Max Bundle Weight Limit')
    direct_credit_reference = fields.Char('Direct Credit Reference')
    area_id = fields.Many2one('res.partner.area', 'Area')
    stock_credit = fields.Boolean('Stock Credit')
    preferred_delivery_type = fields.Selection([('store_drop', 'Store Drop'), ('site_delivery', 'Site Delivery'),
                                                ('pick_up', 'Pick Up'),
                                                ('on_forwarding_address', "On Forwarding Address")],
                                               string='Preferred Delivery Type')
    cover_sheet = fields.Selection([('top', 'Top'),
                                    ('top_bottom', 'Top & Bottom'),
                                    ('na', 'N/A')], string='Cover Sheet')
    charge_freight = fields.Boolean('Charge Freight')
    access_restriction_ids = fields.Many2many('partner.access.restrictions', string='Access Restrictions')
    product_notes_ids = fields.Many2many('partner.product.notes', string='Product Notes')
    lifting_device_ids = fields.Many2many('partner.lifting.device', string='Lifting Device')
    type = fields.Selection(selection_add=[('store_address', 'Store Drop'), ('site_address', 'Site Delivery'),
                                           ('on_forwarding_address', 'On Forwarding Address')])

    def _avatar_get_placeholder_path(self):
        if self.type == 'site_address':
            return "base/static/img/truck.png"
        return super()._avatar_get_placeholder_path()


class PartnerAccessRestrictions(models.Model):
    _name = 'partner.access.restrictions'
    _description = 'Partner Access Restrictions'

    name = fields.Char('Name')


class PartnerProductNotes(models.Model):
    _name = 'partner.product.notes'
    _description = 'Partner Product Notes'

    name = fields.Char('Name')


class PartnerLiftingDevice(models.Model):
    _name = 'partner.lifting.device'
    _description = 'Partner Lifting Device'

    name = fields.Char('Name')
