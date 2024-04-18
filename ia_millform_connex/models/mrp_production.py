# -*- coding: utf-8 -*-

##############################################################################
#    Copyright (C) Ioppolo and Associates (I&A) 2023 (<http://ioppolo.com.au>).
###############################################################################
import json

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from .connex_api_client import ConnexApiClient as Client


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    connex_status = fields.Selection([
        ('not_sent', 'Pending To Be Sent'),
        ('ask_for_status', 'Ask For Status'),
        ('status_received', 'Status Received'),
        ('completed', 'Completed'),
        ('cancel', 'Cancelled'),
    ], default='not_sent', copy=False)

    connex_production_response = fields.Text(string='Connex Response')
    connex_job_id = fields.Char('Connex Job ID', copy=False)
    is_mts = fields.Boolean(string='MTS', default=False)
    connex_workcenter_id = fields.Many2one('mrp.workcenter', 'Work Center', check_company=True)

    def button_send_to_connex(self):
        for mo in self:
            params = {}
            if mo.bom_id:
                if mo.bom_id.connex_workcenter_id and mo.bom_id.connex_workcenter_id.code:
                    params['machine'] = mo.bom_id.connex_workcenter_id.code
            if mo.is_mts:
                mo._send_connex_job_request(params)
            else:
                if not mo.sale_line_id:
                    raise UserError(_("No Sale Order Line linked."))
                mo.sale_line_id._send_connex_job_request(params)
            mo.write({'connex_status': 'ask_for_status'})

    def button_fetch_connex_production(self, production_resposnse=None):
        connex_client = self.env['connex.client']
        for mo in self:
            if not mo.sale_line_id:
                raise UserError(_("No Sale Order Line linked."))
            if not mo.sale_line_id.connex_job_id:
                raise UserError(_("No Connex job ID found."))
            job = connex_client._send_connex_get_job(mo.sale_line_id.connex_job_id)
            if job.get('name', False):
                job_name = job.get('name', '')
                if production_resposnse is None:
                    production_resposnse = connex_client._get_connex_production()
                production_resposnse = [p for p in production_resposnse if
                                        p.get('job', '') == job_name and p.get('length')]
                mo.connex_status = 'status_received' if production_resposnse else 'ask_for_status'
                mo.connex_production_response = json.dumps(production_resposnse, indent=4, sort_keys=True)

    def create_or_search_lot(self, name, product):
        exist_lot = self.env['stock.lot'].search([
            ('product_id', '=', product.id),
            ('company_id', '=', self.company_id.id),
            ('name', '=', name),
        ], limit=1)
        if exist_lot:
            return exist_lot
        else:
            return self.env['stock.lot'].create({
                'name': name,
                'product_id': product.id,
                'company_id': self.company_id.id,
            })

    def button_auto_validate(self):
        connex_client = self.env['connex.client']
        self.ensure_one()
        if not self.connex_production_response:
            return False
        connex_production_response = json.loads(self.connex_production_response)
        connex_production_response = [f for f in connex_production_response if f.get('length')]
        connex_production_response = sorted(connex_production_response, key=lambda d: d['id'])
        processed_ids = []
        if connex_production_response and isinstance(connex_production_response, list):
            data = connex_production_response.pop(0)
            self.qty_producing = round((int(data.get('quantity')) * data.get('length')) * 0.0254, 5)
            self.action_assign()
            material = data.get('material', '').strip()
            lot_name = data.get('coil', '')
            material_product_id = self.env['product.product'].search([('default_code', '=', material)], limit=1)
            lot_id = self.create_or_search_lot(lot_name, material_product_id)
            material_move = self.move_raw_ids.filtered(
                lambda m: m.state not in ('done', 'cancel') and m.product_id == material_product_id)
            bom_line = self.env['mrp.bom.line'].search([('product_id', '=', material_product_id.id)], limit=1)
            if not bom_line:
                raise UserError(_("No BOM found for Material (%s)", str(material)))
            product_qty = self._get_material_consumed_value(bom_line)
            if not material_move:
                # create new move based on product
                move_raw_values = self._get_moves_raw_values_of_material(bom_line)
                material_move = self.env['stock.move'].create(move_raw_values)
            else:
                if float_is_zero(material_move.product_uom_qty, precision_rounding=material_move.product_uom.rounding):
                    material_move.write({'product_uom_qty': product_qty})
                if not material_move.move_line_ids:
                    move_line_vals = material_move._prepare_move_line_vals(quantity=0)
                    move_line_vals['lot_id'] = lot_id.id
                    move_line = self.env['stock.move.line'].create(move_line_vals)
                else:
                    move_line = material_move.move_line_ids[0]
                    move_line.write({'lot_id': lot_id.id})
            material_move.write({'quantity_done': product_qty})
            # make non material moves consumed zero
            non_material_moves = self.move_raw_ids.filtered(lambda m: m.state not in ('done', 'cancel')) - material_move
            for move in non_material_moves:
                if move.product_id != material_product_id:
                    move.product_uom_qty = 0
                    move.quantity_done = 0
            processed_ids.append(str(data.get('id')))
            action = self.with_context(skip_consumption=True).button_mark_done()
            backorder_wizard = self.env["mrp.production.backorder"]
            if isinstance(action, dict) and action.get("res_model") == backorder_wizard._name:
                lines = action.get("context", {}).get(
                    "default_mrp_production_backorder_line_ids"
                )
                mo = action.get("context", {}).get(
                    "'default_mrp_production_ids'"
                )
                backorder_wiz = backorder_wizard.create(
                    {
                        "mrp_production_ids": mo,
                        "mrp_production_backorder_line_ids": lines,
                    }
                )
                backorder_wiz.action_backorder()
                backorder_ids = (
                    self.procurement_group_id.mrp_production_ids.filtered(
                        lambda mo: mo.state not in ["done", "cancel"]
                    )
                )
                current_mo = backorder_ids[0] if backorder_ids else False
                if current_mo:
                    current_mo.sale_line_id = self.sale_line_id and self.sale_line_id.id or False
                    if connex_production_response:
                        current_mo.connex_production_response = json.dumps(connex_production_response, indent=4,
                                                                           sort_keys=True)
                        current_mo.action_assign()
                        current_mo.button_auto_validate()
            if processed_ids:
                """ TODO: CHECK THE RESPONSE IF ALREADY REQUESTED TO CONNEX"""
                connex_client._set_process_connex_production(processed_ids)
                self.write({'connex_status': 'completed'})
        return True

    def _get_material_consumed_value(self, material_bom_line):
        self.ensure_one()
        moves = []
        if not self.bom_id:
            return []
        factor = self.product_uom_id._compute_quantity(self.qty_producing,
                                                       self.bom_id.product_uom_id) / self.bom_id.product_qty
        boms, lines = material_bom_line.bom_id.explode(material_bom_line.bom_id.product_tmpl_id.product_variant_id,
                                                       factor, picking_type=material_bom_line.bom_id.picking_type_id)
        qty = 0
        for bom_line, line_data in lines:
            qty = line_data['qty']
            break
        return qty

    def _get_moves_raw_values_of_material(self, material_bom_line):
        self.ensure_one()
        moves = []
        if not self.bom_id:
            return []
        factor = self.product_uom_id._compute_quantity(self.qty_producing,
                                                       self.bom_id.product_uom_id) / self.bom_id.product_qty
        boms, lines = material_bom_line.bom_id.explode(material_bom_line.bom_id.product_tmpl_id.product_variant_id,
                                                       factor, picking_type=material_bom_line.bom_id.picking_type_id)
        for bom_line, line_data in lines:
            if bom_line.child_bom_id and bom_line.child_bom_id.type == 'phantom' or \
                    bom_line.product_id.type not in ['product', 'consu']:
                continue
            operation = bom_line.operation_id.id or line_data['parent_line'] and line_data[
                'parent_line'].operation_id.id
            moves.append(self._get_move_raw_values(
                bom_line.product_id,
                line_data['qty'],
                bom_line.product_uom_id,
                operation,
                bom_line
            ))
        return moves

    def _send_connex_job_request(self, params=None):
        self.ensure_one()
        if params is None:
            params = {}
        self = self._initiate_client_context()
        connex_client = self.env['connex.client']
        if not self.connex_job_id:
            job_response = self._send_connex_create_job()
            if job_response:
                self.connex_job_id = job_response.get('id', '')
                self._cr.commit()
        self._send_connex_create_batch(job_id=self.connex_job_id)
        machine = params.get('machine', False)
        connex_client._update_profile_details(product_code=self.product_id.default_code, machine=machine, connex_job_id=self.connex_job_id)
        product = self._get_coil_product()
        if product:
            connex_client._send_connex_update_material_details(product.default_code, connex_job_id=self.connex_job_id)

    def _send_connex_create_job(self):
        self.ensure_one()
        data = {
            'name': 'Job - ' + self.name,
        }
        return self.env['connex.client']._send_connex_create_job(data)

    def _send_connex_create_batch(self, job_id):
        self.ensure_one()
        if not job_id:
            job_id = self.connex_job_id
        data = {
            'job': int(job_id),
            'length': round((self.product_id.fixed_length * 1000) / 25.4, 5),
            'quantity': 1,
        }
        return self.env['connex.client']._send_connex_create_batch(job_id, data)

    def _get_coil_product(self):
        self.ensure_one()
        product = self.bom_id.bom_line_ids.mapped('product_id').filtered(lambda p: p.categ_id.name == "SLIT COIL")[:1]
        return product

    def _initiate_client_context(self):
        ctx = self._context.copy()
        new_ctx = self.env['connex.client']._return_client_context()
        ctx.update(new_ctx)
        return self.with_context(ctx)
