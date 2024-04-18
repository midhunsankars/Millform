# -*- coding: utf-8 -*-
import os
from odoo import api, fields, Command, models, exceptions, _

import logging

_logger = logging.getLogger(__name__)


class EdiImportBase(models.AbstractModel):
    _name = 'edi.import.base'
    _description = 'Edi Import Base'

    name = fields.Char()
    file_name = fields.Char('File Name')
    import_file = fields.Binary('Select File', required=True)
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('imported', 'Imported'),
        ],
        string='Status',
        required=True,
        readonly=True,
        copy=False,
        default='draft',
    )
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company)

    @api.model
    def _make_name_pretty(self, name):
        return name.replace("_", " ").capitalize()

    @api.onchange("file_name")
    def _onchange_file_name(self):
        if self.file_name:
            self.name = os.path.splitext(self.file_name)
            self.name = self._make_name_pretty(self.name)

    # -------------------------------------------------------------------------
    # HOOKS
    # -------------------------------------------------------------------------

    def import_file_edi(self):
        """ Hook allow to import csv file"""


class EdiImportConfig(models.Model):
    _name = 'edi.import.config'
    _description = 'Edi Import Config'

    pick_type_id = fields.Many2one('stock.picking.type', 'Pick Type')
    type = fields.Selection(
        selection=[
            ('default', 'Default'),
            ('slit', 'Slit'),
        ],
        string='Type',
        required=True,
        default='default',
    )
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company)
