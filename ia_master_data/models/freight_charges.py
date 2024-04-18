# -*- coding: utf-8 -*-

from odoo import fields, models


class FreightCharges(models.Model):
    _name = 'freight.charges'
    _description = 'Fright Charges'

    product_id = fields.Many2one('product.product', 'Freight Product')
    metro = fields.Boolean('Metro')
    crane = fields.Boolean('Crane')
    longest_length = fields.Integer('Longest Length')
    weight = fields.Integer('Weight')
