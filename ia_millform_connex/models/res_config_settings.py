# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval

from .connex_api_client import ConnexApiClient as Client

PARAMS = (
    ('connex_state', str, 'draft'),
    ('connex_url', str, ''),
    ('connex_user', str, ''),
    ('connex_password', str, ''),
)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    connex_state = fields.Selection(
        [
            ('draft', 'Not Confirmed'),
            ('confirmed', 'Confirmed'),
            ('reconnect', 'Reconnect'),
        ],
        default='draft',
        string="State",
    )

    connex_url = fields.Char(
        string="Connex URL",
    )
    connex_user = fields.Char(
        string="Connex User",
    )
    connex_password = fields.Char(
        string="Connex Password",
    )

    @api.model
    def get_values(self):
        """
        Overwrite to add new system params
        """
        res = super(ResConfigSettings, self).get_values()
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        values = {}
        for field_name, getter, default in PARAMS:
            values[field_name] = getter(str(IrConfigParameter.get_param(field_name, default)))
        res.update(values)
        return res

    def set_values(self):
        """
        Overwrite to add new system params
        """
        super().set_values()
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        for field_name, _, _ in PARAMS:
            value = getattr(self, field_name)
            IrConfigParameter.set_param(field_name, str(value))

    def action_login_connex(self):
        """
        The action to log in Connex Account and confirm permissions

        Returns:
         * Updated config page if test is fine
        """

        Config = self.env['ir.config_parameter'].sudo()
        connex_url = Config.get_param('connex_url', '')
        connex_user = Config.get_param('connex_user', '')
        connex_password = Config.get_param('connex_password', '')
        api_client = Client(connex_url, connex_user, connex_password)
        response = api_client._connex_login()
        if response:
            Config.set_param('connex_state', 'confirmed')

    def action_reset(self):
        """
        The method to remove all data and objects related to connex
        """
        Config = self.env['ir.config_parameter'].sudo()
        for field_name, getter, default in PARAMS:
            Config.set_param(field_name, default)
