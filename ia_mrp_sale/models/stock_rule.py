# -*- coding: utf-8 -*-

##############################################################################
#    Copyright (C) Ioppolo and Associates (I&A) 2023 (<http://ioppolo.com.au>).
###############################################################################

from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _prepare_mo_vals(
        self,
        product_id,
        product_qty,
        product_uom,
        location_id,
        name,
        origin,
        company_id,
        values,
        bom,
    ):
        res = super()._prepare_mo_vals(
            product_id,
            product_qty,
            product_uom,
            location_id,
            name,
            origin,
            company_id,
            values,
            bom,
        )
        res["source_procurement_group_id"] = (
            values.get("group_id").id if values.get("group_id", False) else False
        )
        move_dest_ids = self.env['stock.move']
        if values.get('move_dest_ids'):
            move_dest_ids |= values.get('move_dest_ids')
            sale_line_id = move_dest_ids.mapped('sale_line_id')
            res['sale_line_id'] = sale_line_id[:1].id if sale_line_id[:1] else False
        return res
