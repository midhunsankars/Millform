# -*- coding: utf-8 -*-

##############################################################################
#    Copyright (C) Ioppolo and Associates (I&A) 2023 (<http://ioppolo.com.au>).
###############################################################################

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _update_candidate_moves_list(self, candidate_moves_list):
        """
        We want to merge stock moves within the procurement group only
        """
        res = super()._update_candidate_moves_list(candidate_moves_list)
        if self.env.context.get("sale_group_by_line"):
            candidate_moves_list.append(
                self.sale_line_id.procurement_group_id.stock_move_ids
            )
        return res
