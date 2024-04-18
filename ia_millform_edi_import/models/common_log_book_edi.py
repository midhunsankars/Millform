# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CommonLogBookEdi(models.Model):
    _name = "common.log.book.edi"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = 'id desc'
    _description = "Common log book Edi"

    name = fields.Char(readonly=True)
    type = fields.Selection([('queue_import', 'Queue Import')], string="Operation")
    active = fields.Boolean(default=True)
    log_lines = fields.One2many('common.log.lines.edi', 'log_book_id')
    message = fields.Text()
    model_id = fields.Many2one("ir.model", help="Model Id", string="Model")
    res_id = fields.Integer(string="Record ID", help="Process record id")
    attachment_id = fields.Many2one('ir.attachment', string="Attachment")
    file_name = fields.Char()

    @api.model_create_multi
    def create(self, values):
        seq = self.env['ir.sequence'].next_by_code('common.log.book.edi') or '/'
        values['name'] = seq
        return super(CommonLogBookEdi, self).create(values)

    def create_common_log_book(self, process_type, model_id):
        log_book_id = self.create({"type": process_type,
                                   "model_id": model_id,
                                   "active": True})
        return log_book_id

    def create_common_log_book_ept(self, **kwargs):
        values = {}
        for key, value in kwargs.items():
            if hasattr(self, key):
                values.update({key: value})
        if kwargs.get('model_name'):
            model = self._get_model_id(kwargs.get('model_name'))
            values.update({'model_id': model.id})
        return self.create(values)

    def _get_model_id(self, model_name):
        model_id = self.env['ir.model']
        return model_id.sudo().search([('model', '=', model_name)])
