# -*- coding: utf-8 -*-

##############################################################################
#    Copyright (C) Ioppolo and Associates (I&A) 2023 (<http://ioppolo.com.au>).
###############################################################################

from odoo import fields, models


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    sale_id = fields.Many2one(
        related="production_id.sale_id", string="Sale order", readonly=True, store=True
    )
