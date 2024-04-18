# -*- coding: utf-8 -*-
from odoo import api, fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    skip_confirmation_mail = fields.Boolean(string='Skip Confirmation Mail', default=False)
