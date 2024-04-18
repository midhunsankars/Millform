# -*- coding: utf-8 -*-
import logging
import pytz
import json
import pprint
from odoo import models, fields, api, _

utc = pytz.utc

_logger = logging.getLogger("BulkCoil Order Queue")


class EdiBulkCoilOrderQueue(models.Model):
    _name = "edi.bulk.coil.order.queue"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Edi Bulk Coil Order Queue"

    name = fields.Char(help="Sequential name of imported order.", copy=False)
    state = fields.Selection([('draft', 'Draft'), ('partially_completed', 'Partially Completed'),
                              ('completed', 'Completed'), ('failed', 'Failed')], tracking=True,
                             default='draft', copy=False, compute="_compute_queue_state",
                             store=True)
    order_queue_line_total_record = fields.Integer(string='Total Records',
                                                   compute='_compute_order_queue_line_record')
    order_queue_line_draft_record = fields.Integer(string='Draft Records',
                                                   compute='_compute_order_queue_line_record')
    order_queue_line_fail_record = fields.Integer(string='Fail Records',
                                                  compute='_compute_order_queue_line_record')
    order_queue_line_done_record = fields.Integer(string='Done Records',
                                                  compute='_compute_order_queue_line_record')

    order_queue_line_cancel_record = fields.Integer(string='Cancel Records',
                                                    compute='_compute_order_queue_line_record')
    order_data_queue_line_ids = fields.One2many("edi.bulk.coil.order.queue.line", "bulk_coil_order_queue_id")
    is_process_queue = fields.Boolean('Is Processing Queue', default=False)
    running_status = fields.Char(default="Running...")
    common_log_book_id = fields.Many2one("common.log.book.edi",
                                         help="""Related Log book which has all logs for current queue.""")
    common_log_lines_ids = fields.One2many(related="common_log_book_id.log_lines")

    @api.depends('order_data_queue_line_ids.state')
    def _compute_queue_state(self):
        """
        Computes state from different states of queue lines.
        """
        for record in self:
            if record.order_queue_line_total_record == record.order_queue_line_done_record + \
                    record.order_queue_line_cancel_record:
                record.state = "completed"
            elif record.order_queue_line_draft_record == record.order_queue_line_total_record:
                record.state = "draft"
            elif record.order_queue_line_total_record == record.order_queue_line_fail_record:
                record.state = "failed"
            else:
                record.state = "partially_completed"

    @api.depends('order_data_queue_line_ids.state')
    def _compute_order_queue_line_record(self):
        """This is used for the count of total records of order queue lines
            and display the count records in the form view order data queue.
        """
        for order_queue in self:
            queue_lines = order_queue.order_data_queue_line_ids
            order_queue.order_queue_line_total_record = len(queue_lines)
            order_queue.order_queue_line_draft_record = len(queue_lines.filtered(lambda x: x.state == "draft"))
            order_queue.order_queue_line_done_record = len(queue_lines.filtered(lambda x: x.state == "done"))
            order_queue.order_queue_line_fail_record = len(queue_lines.filtered(lambda x: x.state == "failed"))
            order_queue.order_queue_line_cancel_record = len(queue_lines.filtered(lambda x: x.state == "cancel"))

    @api.model_create_multi
    def create(self, values):
        sequence_id = self.env.ref('ia_millform_edi_import.seq_edi_bulk_coil_order_queue').ids
        if sequence_id:
            record_name = self.env['ir.sequence'].browse(sequence_id).next_by_id()
        else:
            record_name = '/'
        values.update({'name': record_name or ''})
        return super(EdiBulkCoilOrderQueue, self).create(values)

    def import_order_cron_action(self, ctx=False):
        self.edi_create_bulk_coil_order_data_queues()
        return True

    def edi_create_bulk_coil_order_data_queues(self):
        SQL_source = self.env['base.external.dbsource'].search([('connector', '=', 'mssql')], limit=1)
        if not SQL_source:
            return False
        sql_data = SQL_source._execute_mssql(
            sqlquery="SELECT * FROM edi_BulkSlitCoilReceipts WHERE BatchID IS NOT NULL AND TRIM(BatchID) <> '' AND OdooProcessed='N'",
            sqlparams=None, metadata=True)
        if sql_data:
            _logger.info("SQL Data Received \n%s", pprint.pformat(sql_data))
            data_values = []
            sql_data_rows = sql_data[0]
            sql_data_columns = sql_data[1]
            for data_row in sql_data_rows:
                field = list(map(str, data_row))
                value = dict(zip(sql_data_columns, field))
                data_values.append(value)
            if not data_values:
                return False
            # data_values = json.dumps(data_values, indent=4)
            order_queue = self.create({})
            order_data_queue_line_obj = self.env["edi.bulk.coil.order.queue.line"]
            processed_ids = [data.get('ID') for data in data_values]
            for value in data_values:
                order_data_queue_line_obj.create_order_data_queue_line(order_queue, value)
            if processed_ids:
                sqlquery = "UPDATE edi_BulkSlitCoilReceipts set OdooProcessed='%s' WHERE id in %s" % ('Y', tuple(processed_ids),)
                SQL_source._execute_mssql(sqlquery=sqlquery, sqlparams=None, metadata=False, is_update=True)
        return True

    def process_order_queue_manually(self):
        order_queue_ids = self.filtered(
            lambda x: x.state != 'done')
        for order_queue_id in order_queue_ids:
            order_queue_line_ids = order_queue_id.order_data_queue_line_ids.filtered(
                lambda x: x.state in ['draft', 'failed'])
            if order_queue_line_ids:
                order_queue_line_ids.process_import_order_queue_data()
        return True

    def action_view_bulk(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('ia_millform_edi_import.edi_bulk_coil_line_action')
        action['domain'] = [('queue_line_id', 'in', self.order_data_queue_line_ids.ids)]
        return action


class EdiBulkCoilOrderQueueLine(models.Model):
    _name = "edi.bulk.coil.order.queue.line"
    _description = "Edi Bulk Coil Order Queue Line"

    name = fields.Char(help="Batch ID")
    state = fields.Selection([("draft", "Draft"), ("failed", "Failed"), ("done", "Done"),
                              ("cancel", "Cancelled")], default="draft", copy=False)
    bulk_coil_order_queue_id = fields.Many2one("edi.bulk.coil.order.queue", ondelete="cascade")
    order_data = fields.Text(help="Data imported from SQL of current order.", copy=False)
    processed_at = fields.Datetime(help="Shows Date and Time, When the data is processed",
                                   copy=False)
    common_log_lines_ids = fields.One2many("common.log.lines.edi",
                                           "edi_bulk_coil_order_queue_line_id",
                                           help="Log lines created against which line.")

    def create_order_data_queue_line(self, order_queue, value):
        if not order_queue or not value:
            return
        order_queue_line_vals = {
            'name': value.get('BatchID'),
            'bulk_coil_order_queue_id': order_queue.id,
            'order_data': json.dumps(value, indent=4)
        }
        self.create(order_queue_line_vals)

    def process_import_order_queue_data(self):
        edi_bulk_coil_line = self.env["edi.bulk.coil.line"]
        common_log_book_obj = self.env["common.log.book.edi"]
        queue_id = self.bulk_coil_order_queue_id if len(self.bulk_coil_order_queue_id) == 1 else False
        if queue_id:
            if queue_id.common_log_book_id:
                log_book_id = queue_id.common_log_book_id
            else:
                model_id = common_log_book_obj.log_lines.get_model_id("edi.bulk.coil.line")
                log_book_id = common_log_book_obj.create_common_log_book("queue_import", model_id)
            queue_id.is_process_queue = True
            edi_bulk_coil_line.import_edi_orders(self, log_book_id)
            queue_id.write({'is_process_queue': False, 'common_log_book_id': log_book_id})
            if log_book_id and not log_book_id.log_lines:
                log_book_id.unlink()
