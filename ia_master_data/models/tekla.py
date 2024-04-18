# -*- coding: utf-8 -*-

from odoo import fields, models


class TeklaMap(models.Model):
    _name = 'tekla.map'
    _description = 'Tekla Map'

    millform_stockcode = fields.Char('Millform Stockcode')
    supplier_stockcode = fields.Char('Supplier Stockcode')
    supplier_name = fields.Char('Supplier Name')
    centre = fields.Float('Centre')
    v1 = fields.Float('V1')
    v2 = fields.Float('V2')
    u = fields.Float('U')
    o = fields.Float('O')
    h1 = fields.Float('H1')
    h2 = fields.Float('H2')
    ym2_31 = fields.Float('Ym2_31')
    ym1_32 = fields.Float('Ym1_32')
    ym1_33 = fields.Float('Ym1_33')
    ym2_34 = fields.Float('Ym2_34')
    millform_ptype = fields.Float('Millform PType')
    h_ptype = fields.Float('H PType')
