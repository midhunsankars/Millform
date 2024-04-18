# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CommonLogLineEdi(models.Model):
    _name = "common.log.lines.edi"
    _description = "Common log line"

    product_id = fields.Many2one('product.product', 'Product')
    order_ref = fields.Char('Reference')
    log_book_id = fields.Many2one('common.log.book.edi', ondelete="cascade")
    message = fields.Text()
    model_id = fields.Many2one("ir.model", string="Model")
    res_id = fields.Integer("Record ID")
    mismatch_details = fields.Boolean(string='Mismatch Detail', help="Mismatch Detail of process order")
    file_name = fields.Char()
    log_line_type = fields.Selection(selection=[('success', 'Success'), ('fail', 'Fail')],default='fail')

    edi_slit_coil_order_queue_line_id = fields.Many2one("edi.slit.coil.order.queue.line",
                                                        "Edi Slit Coil Order Queue Line")
    edi_bulk_coil_order_queue_line_id = fields.Many2one("edi.bulk.coil.order.queue.line",
                                                        "Edi Bulk Coil Order Queue Line")

    @api.model
    def get_model_id(self, model_name):
        model = self.env['ir.model'].sudo().search([('model', '=', model_name)])
        if model:
            return model.id
        return False

    def create_log_lines(self, message, model_id, res_id, log_book_id, order_ref='', product_id=False):
        vals = {
            'message': message,
            'model_id': model_id,
            'res_id': res_id.id if res_id else False,
            'log_book_id': log_book_id.id if log_book_id else False,
            'order_ref': order_ref,
            'product_id': product_id
        }
        log_line = self.create(vals)
        return log_line

    def create_common_log_line_ept(self, **kwargs):
        values = {}
        for key, value in kwargs.items():
            if hasattr(self, key):
                values.update({key: value})
        if kwargs.get('model_name'):
            model_id = self.log_book_id._get_model_id(kwargs.get('model_name'))
            values.update({'model_id': model_id.id})
        return self.create(values)

    def edi_create_slit_log_line(self, message, model_id, queue_line_id, log_book_id, order_ref=""):
        vals = self.shopify_prepare_log_line_vals(message, model_id, queue_line_id, log_book_id)
        vals.update({
            'edi_slit_coil_order_queue_line_id': queue_line_id and queue_line_id.id or False,
            "order_ref": order_ref if order_ref else queue_line_id.name,
        })
        log_line = self.create(vals)
        return log_line

    def edi_create_bulk_log_line(self, message, model_id, queue_line_id, log_book_id, order_ref=""):
        vals = self.shopify_prepare_log_line_vals(message, model_id, queue_line_id, log_book_id)
        vals.update({
            'edi_bulk_coil_order_queue_line_id': queue_line_id and queue_line_id.id or False,
            "order_ref": order_ref if order_ref else queue_line_id.name,
        })
        log_line = self.create(vals)
        return log_line

    def shopify_prepare_log_line_vals(self, message, model_id, res_id, log_book_id):
        vals = {'message': message,
                'model_id': model_id,
                'res_id': res_id.id if res_id else False,
                'log_book_id': log_book_id.id if log_book_id else False,
                'mismatch_details': self._context.get('is_mismatch_details', False)
                }
        return vals
