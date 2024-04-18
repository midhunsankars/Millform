# -*- coding: utf-8 -*-

from odoo import SUPERUSER_ID, api, fields, models, _
from odoo.addons.sale_management.models.sale_order import SaleOrder as OdooSaleOrder
from odoo.exceptions import ValidationError, UserError
from datetime import datetime

LOCKED_FIELD_STATES = {
    state: [('readonly', True)]
    for state in {'done', 'cancel'}
}


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    delivery_type = fields.Selection([('store_drop', 'Store Drop'), ('site_delivery', 'Site Delivery'),
                                      ('pick_up', 'Pick Up'), ('on_forwarding_address', "On Forwarding Address")],
                                     string='Delivery Type')
    area_id = fields.Many2one('res.partner.area', 'Area')
    ready_to_check = fields.Boolean('Ready to Check')
    checked = fields.Boolean('Checked')
    sent_to_production = fields.Datetime('Sent to Production')
    engineering_narration = fields.Char('Engineering Narration')
    job_reference = fields.Char('Job Reference')
    difot_error = fields.Selection([('0', 'N/A'),
                                    ('1', '1.Production'),
                                    ('2', '2.Loading'),
                                    ('3', '3.Driver'),
                                    ('4', '4.Other')], string='DIFOT Error')
    on_hold = fields.Boolean('On Hold')
    has_request_data = fields.Boolean('Has Request Data')
    partner_cover_sheet = fields.Selection(related='partner_id.cover_sheet')
    freight_charge = fields.Selection([('nil', 'Nil'),
                                       ('site', 'Site'),
                                       ('store', 'Store')], string='Freight Charge')
    crane_required = fields.Boolean('Crane Required')
    time_available = fields.Char('Time Available')
    time_slot = fields.Selection([('std', 'Standard'),
                                  ('non_std', 'Non Standard')], string='Time Slot')

    @api.depends("partner_id")
    def _compute_warehouse_id(self):
        res = super()._compute_warehouse_id()
        for order in self.filtered("partner_id"):
            partner = order.partner_id
            if partner.area_id and partner.area_id.nearest_warehouse_id:
                order.warehouse_id = partner.area_id.nearest_warehouse_id and partner.area_id.nearest_warehouse_id.id or False
        return res

    def action_confirm(self):
        res = super(OdooSaleOrder, self).action_confirm()
        if self.env.su:
            self = self.with_user(SUPERUSER_ID)

        for order in self.filtered('partner_id'):
            if order.partner_id.skip_confirmation_mail:
                continue
            if order.sale_order_template_id and order.sale_order_template_id.mail_template_id:
                order.sale_order_template_id.mail_template_id.send_mail(order.id)
        return res


OdooSaleOrder.action_confirm = SaleOrder.action_confirm


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    so_line_lengths = fields.One2many('so.line.lengths', 'so_line_id', 'SO Line Lengths')
    so_line_bundles = fields.One2many('so.line.bundles', 'so_line_id', 'SO Line Bundles')
    stock_code = fields.Char(string='Stock Code', related='product_id.default_code')
    can_be_punched = fields.Selection(related='product_id.can_be_punched')
    is_punched = fields.Boolean('Is Punched?')
    packs = fields.Integer('Packs')
    rack_no = fields.Char('Rack No')
    machine_number = fields.Integer('Machine Number')
    mlock = fields.Boolean('MLock')
    spec_mrp_notes = fields.Char('Specific Manufacturing Notes')
    manufactured = fields.Boolean('Manufactured')
    manufactured_time = fields.Datetime('Manufactured Time')
    tick_urgent = fields.Boolean('Urgent')
    wrap_in_plastic = fields.Boolean('Wrap in Plastic')
    ams_id = fields.Integer('AMS ID')
    bundle_ref = fields.Char('Bundle Ref')
    qty_per_pack = fields.Float('Qty per Pack')
    line_12_step = fields.Float('Line 12 Step', digits=(12, 3))
    bundle_limit_t = fields.Float('Bundle Limit T')
    bundle_step = fields.Float('Bundle Step')
    cover_sheet_available = fields.Selection(related='product_id.cover_sheet_available')
    partner_cover_sheet = fields.Selection(related='order_id.partner_cover_sheet')
    sticker_print_option = fields.Selection([('0', 'Do Nothing'),
                                             ('1', 'Create label or Reprint'),
                                             ('2', 'Rebundle and AMS')], string='Sticker Print Option')
    cover_sheet = fields.Selection([('top', 'Top'),
                                    ('top_bottom', 'Top & Bottom'),
                                    ('na', 'N/A')], string='Sale Cover Sheet')

    def open_form(self):
        return {
            'res_model': 'sale.order.line',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('ia_sale.ia_sale_order_lines').id,
            'res_id': self.id
        }

    total_quantity = fields.Float('Total Quantity', compute='_compute_total_length')
    total_meter = fields.Float('Total Meter', compute='_compute_total_length')
    reduce_meter = fields.Float('Reduce Meter', compute='_compute_total_length')

    def _compute_total_length(self):
        for line in self:
            total_quantity = 0.0
            total_meter = 0.0
            reduce_meter = 0.0
            for length in line.so_line_lengths:
                total_quantity += length.quantity
                total_meter += (length.quantity * length.length)
                reduce_meter += (length.quantity * (length.length - line.product_id.bridging_reduce_by))
            line.total_quantity = total_quantity
            line.total_meter = total_meter
            line.reduce_meter = reduce_meter


class SOLineLengths(models.Model):
    _name = 'so.line.lengths'
    _description = 'So Line Lengths'
    _rec_name = 'complete_name'

    so_line_id = fields.Many2one('sale.order.line', 'SO Line ID')
    quantity = fields.Float('Quantity', digits=(12, 0))
    length = fields.Float('Length', digits=(12, 3))
    marking = fields.Char('Marking')
    so_line_lengths_punch = fields.One2many('so.line.lengths.punch', 'so_line_length_id', 'SO Line Lengths Punch')
    complete_name = fields.Char('Complete Name', compute='_compute_complete_name', store=True)

    @api.depends('so_line_id', 'quantity')
    def _compute_complete_name(self):
        for length in self:
            complete_name = '/'
            if length.so_line_id:
                complete_name = length.so_line_id.order_id.name
                if length.quantity:
                    complete_name = '%s / %s' % (complete_name, str(length.quantity))
            length.complete_name = complete_name


class SOLineLengthsPunch(models.Model):
    _name = 'so.line.lengths.punch'
    _description = 'So Line Lengths Punch'

    so_line_length_id = fields.Many2one('so.line.lengths', 'SO Line Length ID', ondelete='cascade')
    dimension = fields.Float('Dimension', digits=(12, 3))
    punch_type = fields.Char('Punch Types')
    punch_type_id = fields.Many2one('so.punch.type', 'Punch Type')
    y_plus1 = fields.Float('Y-Plus1')
    y_minus1 = fields.Float('Y-Minus1')
    y_plus2 = fields.Float('Y-Plus2')
    y_minus2 = fields.Float('Y-Minus2')


class SOPunchType(models.Model):
    _name = 'so.punch.type'
    _description = 'So Punch Type'

    name = fields.Char('Sequence')
    description = fields.Char('Description')
    press_number = fields.Integer('Press Number')
    punch_name = fields.Integer('Punch Number')
    y_plus_1 = fields.Float('Y Plus 1')
    y_minus_1 = fields.Float('Y Minus 1')
    y_plus_2 = fields.Float('Y Plus 2')
    y_minus_2 = fields.Float('Y Minus 2')
    punchanywhereoption = fields.Integer('Punch Anywhere Option')
    victorian_punching70mm = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Victorian Punching 70mm')
    std_ends_center = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Std Ends Center')
    edit_y_dims = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Edit Y Dims')
    stock_code = fields.Char('Stock Code')
    product_id = fields.Many2one('product.product', 'Product')
    active = fields.Boolean('Active')


class SOLineBundles(models.Model):
    _name = 'so.line.bundles'
    _description = 'So Line Bundles'

    so_line_id = fields.Many2one('sale.order.line', 'SO Line ID')
    pack = fields.Float('Pack', digits=(12, 0))
    total_pack = fields.Float('Total Packs', digits=(12, 0))
    pack_qty = fields.Float('Pack Quantity', digits=(12, 3))
    longest_length = fields.Float('Longest Length', digits=(12, 3))
    weight = fields.Float('Weight', digits=(12, 3))
    so_line_bundle_lines = fields.One2many('so.line.bundles.lines', 'so_line_bundle_id', 'SO Line Bundle Lines')


class SOLineBundleLines(models.Model):
    _name = 'so.line.bundles.lines'
    _description = 'So Line Bundles Lines'

    so_line_bundle_id = fields.Many2one('so.line.bundles', 'SO Line Bundle ID', ondelete='cascade')
    so_line_length_id = fields.Many2one('so.line.lengths', 'SO Line Length ID')
    quantity = fields.Float('Quantity', digits=(12, 0))
    length = fields.Float('Length', digits=(12, 3))
    marking = fields.Char('Marking')


class ProductCategory(models.Model):
    _inherit = 'product.category'

    bridging = fields.Boolean(string='Bridging', default=False)


class MrpProduction(models.Model):
    """ Manufacturing Orders """
    _inherit = 'mrp.production'

    def _get_move_raw_values(self, product_id, product_uom_qty, product_uom, operation_id=False, bom_line=False):
        data = super()._get_move_raw_values(product_id=product_id, product_uom_qty=product_uom_qty,
                                            product_uom=product_uom, operation_id=operation_id, bom_line=bom_line)
        if self.product_id.categ_id.bridging:
            sale_order_ids = self.procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id
            if sale_order_ids:
                if product_uom.name == 'M':
                    data['product_uom_qty'] = sale_order_ids[0].order_line.filtered(
                        lambda m: m.product_id == self.product_id).reduce_meter
                elif product_uom.name == 'EA':
                    bom_line_id = self.env['mrp.bom.line'].browse(data['bom_line_id'])
                    data['product_uom_qty'] = (sale_order_ids[0].order_line.filtered(
                        lambda m: m.product_id == self.product_id).total_quantity) * bom_line_id.product_qty
        return data
