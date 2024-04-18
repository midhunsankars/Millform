# -*- coding: utf-8 -*-

##############################################################################
#    Copyright (C) Ioppolo and Associates (I&A) 2023 (<http://ioppolo.com.au>).
###############################################################################

from odoo import api, fields, models, _


class ProductCategory(models.Model):
    _inherit = 'product.category'

    is_send_to_connex = fields.Boolean(string='Send to Connex', default=False)
