# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from .connex_api_client import ConnexApiClient as Client

GLOBAL_VARIABLES = {'dimension_1': 31, 'dimension_2': 88}


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_created_from_symphony = fields.Boolean(default=False)

    def write(self, values):
        res = super(SaleOrder, self).write(values)
        if values is not None:
            for order in self:
                if order.is_created_from_symphony:
                    raise UserError(_("Sale Order Is not Editable, Please contact an Administrator"))
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    connex_job_id = fields.Char('Connex Job ID', copy=False)

    def _send_connex_job_request(self, params=None):
        if params is None:
            params = {}
        self = self._initiate_client_context()
        connex_client = self.env['connex.client']
        for line in self:
            if not line.so_line_lengths or not line.so_line_bundles:
                return
            if not line.connex_job_id:
                job_response = line._send_connex_create_job()
                line.connex_job_id = job_response.get('id', '') if job_response else False
                self._cr.commit()
            product, width = line._get_coil_product_width()
            for bundle in line.so_line_bundles:
                for line_bundle in bundle.so_line_bundle_lines:
                    if line_bundle.so_line_length_id:
                        line_bundle.so_line_length_id._create_parts(width=width)
                    if not line_bundle.connex_batch_id:
                        batch_response = line_bundle._send_connex_create_batch(job_id=self.connex_job_id)
                        line_bundle.connex_batch_id = batch_response.get('id', '') if batch_response else False
            self._cr.commit()
            machine = params.get('machine', False)
            connex_client._update_profile_details(product_code=self.product_id.default_code, machine=machine, connex_job_id=line.connex_job_id)
            if product:
                connex_client._send_connex_update_material_details(product.default_code, connex_job_id=line.connex_job_id)

    def _send_connex_create_job(self):
        self.ensure_one()
        data = {
            'name': 'Job - ' + self.order_id.name,
            'udf2': self.order_id.name,
            'udf1': self.order_id.partner_id.name,
            'udf3': 'SO : ' + self.order_id.name,
            'udf7': self.order_id.client_order_ref or '',
            'udf9': self.order_id.area_id and self.order_id.area_id.name or '',
            'udf10': '',
        }
        if self.order_id.partner_shipping_id:
            delivery_add = ' '.join([x for x in [self.order_id.partner_shipping_id.city,
                                                 self.order_id.partner_shipping_id.state_id.code,
                                                 self.order_id.partner_shipping_id.zip] if x])
            data.update(udf6=delivery_add)
        return self.env['connex.client']._send_connex_create_job(data)

    def _initiate_client_context(self):
        ctx = self._context.copy()
        new_ctx = self.env['connex.client']._return_client_context()
        ctx.update(new_ctx)
        return self.with_context(ctx)

    def _get_coil_product_width(self):
        self.ensure_one()
        bom = \
        self.env['mrp.bom'].with_context(active_test=True)._bom_find(self.product_id, company_id=self.company_id.id,
                                                                     bom_type='normal')[
            self.product_id]
        product = bom.bom_line_ids.mapped('product_id').filtered(lambda p: p.categ_id.name == "SLIT COIL")[:1]
        return product, product.coil_width or 0.0


class SOLineBundleLines(models.Model):
    _inherit = 'so.line.bundles.lines'

    connex_batch_id = fields.Char('Connex Batch ID', copy=False)

    def _send_connex_create_batch(self, job_id):
        self.ensure_one()
        connex_client = self.env['connex.client']
        if not job_id:
            job_id = self.so_line_bundle_id.so_line_id.connex_job_id
        data = {
            'job': int(job_id),
            'length': round((self.length * 1000) / 25.4, 5),
            'udf1': self.marking,
            'udf4': self.so_line_bundle_id.pack_qty,
            'quantity': self.quantity,
        }
        if self.so_line_bundle_id.pack:
            data.update({'name': str(int(self.so_line_bundle_id.pack))})
        if self.so_line_length_id and self.so_line_length_id.connex_part_id:
            part_details = connex_client._send_connex_get_part_name(self.so_line_length_id.connex_part_id)
            data.update({'part': part_details.get('name', 'Shear Only')})
        return connex_client._send_connex_create_batch(job_id, data)


class SOLineLengths(models.Model):
    _inherit = 'so.line.lengths'

    connex_part_id = fields.Char('Connex Part ID', copy=False)

    def _create_parts(self, width=0):
        self.ensure_one()
        if not self.so_line_lengths_punch:
            return
        if not self.connex_part_id:
            part_response = self._send_connex_create_part()
            if part_response:
                self.connex_part_id = part_response.get('id', '')
                self._cr.commit()
            self.so_line_lengths_punch._create_operation(part=self.connex_part_id, width=width)
            self._cr.commit()

    def _send_connex_create_part(self):
        self.ensure_one()
        data = {
            "description": self.so_line_id.order_id.name or '',
            "name": '{}-{}'.format(self.id, self.so_line_id.id or ''),
        }
        return self.env['connex.client']._send_connex_create_part(data)


class SOLineLengthsPunch(models.Model):
    _inherit = 'so.line.lengths.punch'

    connex_operation_plus1_id = fields.Char('Connex Operation Plus1 ID', copy=False)
    connex_operation_minus1_id = fields.Char('Connex Operation Minus1 ID', copy=False)
    connex_operation_plus2_id = fields.Char('Connex Operation Plus2 ID', copy=False)
    connex_operation_minus2_id = fields.Char('Connex Operation Minus2 ID', copy=False)

    def _create_operation(self, part=None, width=0):
        if not part:
            return
        connex_client = self.env['connex.client']
        order_number = 0
        for operation in self:
            data = {
                "part": int(part),
                "y_position": 0,
                "position": round((operation.dimension * 1000) / 25.4, 5),
            }
            if operation.punch_type_id and operation.punch_type_id.punch_name == 35:

                data_minus2 = dict(data, order_number=order_number, name="31")
                if int(operation.y_minus2) != 999:
                    data_minus2.update(y_position=round((operation.y_minus2 / 25.4), 5))
                else:
                    y_position = (width / 2)
                    if int(operation.y_minus1) == 999:
                        y_position += (GLOBAL_VARIABLES.get('dimension_2', 88))
                    else:
                        y_position += (GLOBAL_VARIABLES.get('dimension_1', 31))
                    data_minus2.update(
                        y_position=round((y_position / 25.4), 5)
                    )
                operation_response_minus2 = connex_client._send_connex_create_operation(data_minus2)
                if operation_response_minus2:
                    operation.connex_operation_minus2_id = operation_response_minus2.get('id', '')
                order_number += 1

                data_minus1 = dict(data, y_position=round((operation.y_minus1 / 25.4), 5),
                                   order_number=order_number, name="32")
                if int(operation.y_minus1) == 999 and width:
                    y_position = (width / 2)
                    y_position += (GLOBAL_VARIABLES.get('dimension_1', 31))
                    data_minus1.update(
                        y_position=round((y_position / 25.4), 5)
                    )
                operation_response_minus1 = connex_client._send_connex_create_operation(data_minus1)
                if operation_response_minus1:
                    operation.connex_operation_minus1_id = operation_response_minus1.get('id', '')
                order_number += 1

                data_plus1 = dict(data, y_position=round((operation.y_plus1 / 25.4), 5), order_number=order_number,
                                  name="33")
                if int(operation.y_plus1) == 999 and width:
                    y_position = (width / 2) + GLOBAL_VARIABLES.get('dimension_1', 33)
                    data_plus1.update(
                        y_position=round((y_position / 25.4), 5)
                    )
                operation_response_plus1 = connex_client._send_connex_create_operation(data_plus1)
                if operation_response_plus1:
                    operation.connex_operation_plus1_id = operation_response_plus1.get('id', '')
                order_number += 1

                data_plus2 = dict(data, order_number=order_number, name="34")
                if int(operation.y_plus2) != 999:
                    data_plus2.update(y_position=round((operation.y_plus2 / 25.4), 5))
                else:
                    y_position = (width / 2)
                    if int(operation.y_plus1) == 999:
                        y_position += (GLOBAL_VARIABLES.get('dimension_2', 88))
                    else:
                        y_position += (GLOBAL_VARIABLES.get('dimension_1', 31))
                    data_plus2.update(
                        y_position=round((y_position / 25.4), 5)
                    )
                operation_response_plus2 = connex_client._send_connex_create_operation(data_plus2)
                if operation_response_plus2:
                    operation.connex_operation_plus2_id = operation_response_plus2.get('id', '')
                order_number += 1
            else:
                data_plus1 = dict(data, y_position=round((operation.y_plus1 / 25.4), 5), order_number=order_number)
                operation_response_plus1 = connex_client._send_connex_create_operation(data_plus1)
                if operation_response_plus1:
                    operation.connex_operation_plus1_id = operation_response_plus1.get('id', '')
                order_number += 1
