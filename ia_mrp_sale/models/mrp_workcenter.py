# -*- coding: utf-8 -*-

##############################################################################
#    Copyright (C) Ioppolo and Associates (I&A) 2023 (<http://ioppolo.com.au>).
###############################################################################

from odoo import api, fields, models, _


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    gauge_time = fields.Float('Gauge time')
    width_time = fields.Float('Width time')
    run_speed = fields.Float('Run Speed')
    short_run_speed = fields.Float('Short Run Speed')
    short_length = fields.Float('Short Length')
    pack_time = fields.Float('Pack Time')

    def name_get(self):
        name_list = []
        for record in self:
            name = record.name
            if record.code:
                name += ' (%s)' % record.code
            name_list += [(record.id, name)]
        return name_list
