# -*- coding: utf-8 -*-

##############################################################################
#    Copyright (C) Ioppolo and Associates (I&A) 2023 (<http://ioppolo.com.au>).
###############################################################################

from odoo import fields, models


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    connex_workcenter_id = fields.Many2one('mrp.workcenter', 'Work Center', check_company=True)
