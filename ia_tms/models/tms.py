# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
import ast

from math import radians, cos, sin, asin, sqrt


class Trucks(models.Model):
    _name = 'tms.trucks'
    _description = "Trucks"

    name = fields.Char('Description')
    rego = fields.Char('Rego')
    capacity = fields.Float('Capacity (T)')
    product_id = fields.Many2one('product.product', 'Product', domain=[('detailed_type', '=', 'service')])
    partner_id = fields.Many2one('res.partner', 'Vendor')
    mf_owned = fields.Selection([('yes', 'Yes'),
                                 ('no', 'No')], string='Millform Owned')
    rate_km = fields.Float('Rate (per km)')


class Trailers(models.Model):
    _name = 'tms.trailers'
    _description = "Trailers"

    name = fields.Char('Description')
    rego = fields.Char('Rego')
    capacity = fields.Float('Capacity (T)')
    mf_owned = fields.Selection([('yes', 'Yes'),
                                 ('no', 'No')], string='Millform Owned')
    rate_trailer = fields.Float('Rate (per km)')
    max_length = fields.Float('Max Length')
    product_id = fields.Many2one('product.product', 'Product', domain=[('detailed_type', '=', 'service')])
    partner_id = fields.Many2one('res.partner', 'Vendor')


class Drivers(models.Model):
    _name = 'tms.drivers'
    _description = "Drivers"

    name = fields.Char('Name')
    mobile = fields.Char('Mobile')
    mf_driver = fields.Selection([('yes', 'Yes'),
                                  ('no', 'No')], string='Millform Driver')
    rate_km = fields.Float('Rate (per km)')
    rate_drop = fields.Float('Rate (per drop)')
    product_id = fields.Many2one('product.product', 'Product', domain=[('detailed_type', '=', 'service')])
    partner_id = fields.Many2one('res.partner', 'Vendor')


class Loads(models.Model):
    _name = 'tms.loads'
    _description = "Loads"

    name = fields.Char('Load Reference')
    load_date = fields.Datetime('Load Date')
    delivery_date = fields.Date('Delivery Date')
    load_time = fields.Char('Load Time')
    load_duration_hrs = fields.Float('Load Duration Hrs')
    load_leave_days = fields.Integer('Load Leave Days')
    load_leave_date = fields.Date('Load Leave Date', compute='_compute_load_leave_date')
    driver_id = fields.Many2one('tms.drivers', 'Driver')
    truck_id = fields.Many2one('tms.trucks', 'Truck')
    trailer_ids = fields.Many2many('tms.trailers', 'load_trailers_rel', 'load_id', 'trailer_id', string='Trailers')
    origin_id = fields.Many2one('stock.warehouse', 'Origin')
    destination_id = fields.Many2one('stock.warehouse', 'Destination')
    area_ids = fields.Many2many('res.partner.area', 'load_areas_rel', 'load_id', 'area_id', string='Areas')
    capacity = fields.Float('Capacity (T)', compute='_compute_capacity')
    length = fields.Float('Length')
    main_type = fields.Selection([('delivery', 'Delivery'),
                                  ('transfer', 'Transfer'),
                                  ('pickup', 'Pickup')], string='Transfer Type')
    load_line_details_ids = fields.One2many('stock.move', 'load_id', copy=False)
    load_line_ids = fields.One2many('tms.loads.lines', 'load_id', copy=False)
    state = fields.Selection([('new', 'New'),
                              ('in_transit', 'In Transit'),
                              ('completed', 'Completed')], default='new', string='Status')
    total_km = fields.Float('Total Km')

    @api.depends('trailer_ids')
    def _compute_capacity(self):
        for rec in self:
            capacity = 0
            for lines in rec.trailer_ids:
                capacity += lines.capacity
            rec.capacity = capacity

    @api.depends('load_date', 'load_leave_days')
    def _compute_load_leave_date(self):
        load_leave_date = False
        for rec in self:
            if rec.load_date:
                load_leave_date = rec.load_date + relativedelta(days=rec.load_leave_days)
            rec.load_leave_date = load_leave_date

    @api.model_create_multi
    def create(self, values):
        values['name'] = self.env['ir.sequence'].next_by_code('tms.loads')
        return super(Loads, self).create(values)

    def button_allocate(self):
        for rec in self:
            if not rec.load_line_ids:
                raise UserError('Load lines is not available')
            rec.write({'state': 'in_transit'})

    def button_complete(self):
        for rec in self:
            if not rec.load_line_ids:
                raise UserError('Load lines is not available')
            rec.write({'state': 'completed'})

    def button_create_po(self):
        for rec in self:
            if not rec.load_line_ids:
                raise UserError('Load lines is not available')

            order_lines = []
            partner_id = False
            PurchaseOrder = self.env['purchase.order']

            if rec.truck_id.mf_owned == 'no':
                order_lines.append((0, 0, {
                    'product_id': rec.truck_id.product_id.id,
                    'product_qty': rec.total_km,
                    'price_unit': rec.truck_id.rate_km,
                }))
            if order_lines:
                partner_ids = rec.trailer_ids.sorted('partner_id').mapped('partner_id')
                partner_id = rec.truck_id.partner_id.id
                if partner_id not in partner_ids.ids or partner_id != rec.driver_id.partner_id.id:
                    PurchaseOrder.create({
                        'partner_id': rec.truck_id.partner_id.id,
                        'origin': rec.name,
                        'order_line': order_lines,
                    })
                    order_lines = []
                    partner_id = False
            else:
                order_lines = []
                partner_id = False
            if rec.driver_id.mf_driver == 'no':
                order_lines.append((0, 0, {
                    'product_id': rec.driver_id.product_id.id,
                    'product_qty': rec.total_km,
                    'price_unit': rec.driver_id.rate_km,
                }))
            if order_lines:
                partner_ids = rec.trailer_ids.sorted('partner_id').mapped('partner_id')
                partner_id = rec.driver_id.partner_id.id
                if rec.driver_id.partner_id.id not in partner_ids.ids:
                    PurchaseOrder.create({
                        'partner_id': rec.truck_id.partner_id.id,
                        'origin': rec.name,
                        'order_line': order_lines,
                    })
                    order_lines = []
                    partner_id = False
            else:
                order_lines = []
                partner_id = False
            for trailer_id in rec.trailer_ids.sorted('partner_id'):
                if trailer_id.mf_owned == 'no':
                    if partner_id != trailer_id.partner_id.id:
                        if partner_id and order_lines:
                            PurchaseOrder.create({
                                'partner_id': rec.truck_id.partner_id.id,
                                'origin': rec.name,
                                'order_line': order_lines,
                            })
                        order_lines = []
                        partner_id = trailer_id.partner_id.id
                    order_lines.append((0, 0, {
                        'product_id': trailer_id.product_id.id,
                        'product_qty': rec.total_km,
                        'price_unit': trailer_id.rate_trailer,
                    }))

            if rec.trailer_ids and order_lines:
                PurchaseOrder.create({
                    'partner_id': rec.truck_id.partner_id.id,
                    'origin': rec.name,
                    'order_line': order_lines,
                })


class LoadLines(models.Model):
    _name = 'tms.loads.lines'
    _description = "Load Lines"
    _order = 'sequence, id'

    load_id = fields.Many2one('tms.loads', 'Load ID')
    sequence = fields.Integer("Sequence", default=10)
    transfer_group = fields.Integer("Transfer Group", default=1)
    transfer_id = fields.Many2one('stock.picking', 'Stock Transfer')
    partner_id = fields.Many2one('res.partner', 'Customer')
    delivery_partner_id = fields.Many2one('res.partner', 'Delivery Address')
    delivery_date = fields.Datetime('Delivery Date')
    type = fields.Selection([('delivery', 'Delivery'),
                             ('transfer', 'Transfer'),
                             ('pickup', 'Pickup')], string='Transfer Type')
    customer_notes = fields.Text('Customer Notes')
    partner_latitude = fields.Float('Geo Latitude', digits=(10, 7))
    partner_longitude = fields.Float('Geo Longitude', digits=(10, 7))
    bundle_ids = fields.Char('Bundle Details', default="[]")
    total_km = fields.Float('Total Km', compute='_compute_haversine')

    @api.depends('sequence', 'load_id')
    def _compute_haversine(self):
        """Function to compute line numbers"""
        for order in self.mapped('load_id'):
            sequence_number = 1
            total_km = 0.0
            delivery_partner_id = []
            lon1 = order.origin_id.partner_id.partner_longitude
            lat1 = order.origin_id.partner_id.partner_latitude
            for line in order.load_line_ids:
                if line.delivery_partner_id.id not in delivery_partner_id:
                    delivery_partner_id.append(line.delivery_partner_id.id)
                    line.transfer_group = delivery_partner_id.index(line.delivery_partner_id.id) + 1
                else:
                    line.transfer_group = delivery_partner_id.index(line.delivery_partner_id.id) + 1
                if sequence_number > 1:
                    lon1 = lon2
                    lat1 = lat2
                lon2 = line.partner_longitude
                lat2 = line.partner_latitude
                line.total_km = self._compute_haversine_formula(lon1, lat1, lon2, lat2)
                sequence_number += 1
                total_km = total_km + line.total_km
            if sequence_number > 1:
                lon1 = lon2
                lat1 = lat2
            lon2 = order.destination_id.partner_id.partner_longitude
            lat2 = order.destination_id.partner_id.partner_latitude
            total_km = total_km + self._compute_haversine_formula(lon1, lat1, lon2, lat2)
            order.total_km = total_km

    def _compute_haversine_formula(self, lon1, lat1, lon2, lat2):
        """
        Calculate the great circle distance in kilometers between two points 
        on the earth (specified in decimal degrees)
        """
        # convert decimal degrees to radians 
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        # haversine formula 
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
        return round(c * r, 2)

    def open_form(self):
        for rec in self:
            return {
                'res_model': 'so.line.bundles',
                'type': 'ir.actions.act_window',
                'view_mode': 'tree',
                'view_id': self.env.ref('ia_tms.ia_tms_view_bundle_tree').id,
                'domain': [('id', 'in', ast.literal_eval(rec.bundle_ids))],
                'target': 'new'
            }
