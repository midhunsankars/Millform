# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from .connex_api_client import ConnexApiClient as Client


class ConnexClient(models.AbstractModel):
    _name = "connex.client"
    _description = "Connex Client"

    def _send_connex_create_job(self, data=None):
        if data is None:
            data = {}
        _data = {
            'machine': 'Undefined',
            'location': 'Undefined',
            'material': 'Undefined',
            'profile': 'Undefined',
        }
        data.update(_data)
        try:
            client = self._context.get("client")
            res = client._connex_create_job(data)
        except Exception as error:
            if type(error).__name__ == "MissingError":
                # 1
                res = {}
            else:
                res = None
                raise UserError(_(
                    u"Failed to create job details"
                ))
        return res

    def _send_connex_get_job(self, connex_job_id=None):
        if connex_job_id is None:
            return {}
        if not self._context.get("client", False):
            self = self._initiate_client_context()
        try:
            client = self._context.get("client")
            res = client._connex_get_job(connex_job_id)
        except Exception as error:
            if type(error).__name__ == "MissingError":
                # 1
                res = {}
            else:
                res = None
                raise UserError(_(
                    u"Failed to get job details"
                ))
        return res

    def _send_connex_update_job(self, data=None, connex_job_id=None):
        if connex_job_id is None or data is None:
            return {}
        
        try:
            client = self._context.get("client")
            res = client._connex_update_job(data, connex_job_id)

        except Exception as error:
            if type(error).__name__ == "MissingError":
                # 1
                res = {}
            else:
                res = None
                raise UserError(_(
                    u"Failed to update job"
                ))
        return res

    def _send_connex_create_batch(self, job_id=None, data=None):
        if not job_id or not data:
            return {}
        try:
            client = self._context.get("client")
            res = client._connex_create_batch(data)
        except Exception as error:
            if type(error).__name__ == "MissingError":
                # 1
                res = {}
            else:
                res = None
                raise UserError(_(
                    u"Failed to create batch details"
                ))
        return res

    def _send_connex_create_part(self, data=None):
        if not data:
            return {}
        try:
            client = self._context.get("client")
            res = client._connex_create_part(data)
        except Exception as error:
            if type(error).__name__ == "MissingError":
                # 1
                res = {}
            else:
                res = None
                raise UserError(_(
                    u"Failed to create part details"
                ))
        return res

    def _send_connex_get_part_name(self, connex_part_id=None):
        if connex_part_id is None:
            return {}
        try:
            client = self._context.get("client")
            res = client._connex_get_part(connex_part_id)
        except Exception as error:
            if type(error).__name__ == "MissingError":
                # 1
                res = {}
            else:
                res = None
                raise UserError(_(
                    u"Failed to get part details"
                ))
        return res

    def _send_connex_create_operation(self, data=None):
        if not data:
            return {}
        try:
            client = self._context.get("client")
            res = client._connex_create_operation(data)
        except Exception as error:
            if type(error).__name__ == "MissingError":
                # 1
                res = {}
            else:
                res = None
                raise UserError(_(
                    u"Failed to create operation details"
                ))
        return res

    def _update_profile_details(self, product_code=None, machine=None, connex_job_id=None):
        data = {}
        if not product_code or not connex_job_id:
            return
        is_profile = self._send_connex_get_profile(product_code)
        if not is_profile:
            job_profile = self._send_connex_create_profile(product_code)
            profile = job_profile.get('name', '')
            profile_id = job_profile.get('id', '')
        else:
            profile = product_code
            profile_id = is_profile[0].get('id', '')
        data['profile'] = profile
        if machine:
            is_machine = self._send_connex_get_machine(machine)
            if not is_machine:
                job_machine = self._send_connex_create_machine(machine)
            is_machine_profile = self._send_connex_get_machine_profile(profile_id, machine)
            if not is_machine_profile:
                job_machine_profile = self._send_connex_create_machine_profile(product_code, machine)
            data['machine'] = machine
        self._send_connex_update_job(data=data, connex_job_id=connex_job_id)

    def _send_connex_get_profile(self, product_code):
        if not product_code:
            return []
        try:
            client = self._context.get("client")
            res = client._connex_get_profile({'name': product_code})
        except Exception as error:
            if type(error).__name__ == "MissingError":
                # 1
                res = []
            else:
                res = None
                raise UserError(_(
                    u"Failed to get profile details"
                ))
        res = [r for r in res if r.get('name', '') == product_code]
        return res

    def _send_connex_create_profile(self, product_code):
        if not product_code:
            return {}
        data = {
            'name': product_code
        }
        try:
            client = self._context.get("client")
            res = client._connex_create_profile(data)

        except Exception as error:
            if type(error).__name__ == "MissingError":
                # 1
                res = {}
            else:
                res = None
                raise UserError(_(
                    u"Failed to create profile details"
                ))
        return res

    def _send_connex_get_machine(self, machine):
        if not machine:
            return {}
        try:
            client = self._context.get("client")
            res = client._connex_get_machine({'name': machine})
        except Exception as error:
            if type(error).__name__ == "MissingError":
                # 1
                res = []
            else:
                res = None
                raise UserError(_(
                    u"Failed to get machine details"
                ))
        if not res:
            return []
        res = [r for r in res if r.get('name', '') == machine]
        return res

    def _send_connex_create_machine(self, machine):
        if not machine:
            return {}
        data = {
            'name': machine
        }
        try:
            client = self._context.get("client")
            res = client._connex_create_machine(data)

        except Exception as error:
            if type(error).__name__ == "MissingError":
                # 1
                res = {}
            else:
                res = None
                raise UserError(_(
                    u"Failed to create machine details"
                ))
        return res

    def _send_connex_get_machine_profile(self, profile_id, machine):
        if not machine or not profile_id:
            return []
        try:
            client = self._context.get("client")
            res = client._connex_get_machine_profile({'profile': profile_id})
        except Exception as error:
            if type(error).__name__ == "MissingError":
                # 1
                res = []
            else:
                res = None
                raise UserError(_(
                    u"Failed to get machine profile details"
                ))
        if not res:
            return []
        res = [r for r in res if r.get('machine', '') == machine]
        return res

    def _send_connex_create_machine_profile(self, profile, machine):
        if not machine or not profile:
            return {}
        data = {
            'profile': profile,
            'machine': machine
        }
        try:
            client = self._context.get("client")
            res = client._connex_create_machine_profile(data)

        except Exception as error:
            if type(error).__name__ == "MissingError":
                # 1
                res = {}
            else:
                res = None
                raise UserError(_(
                    u"Failed to get machine profile details"
                ))
        return res

    def _send_connex_update_material_details(self, product_code, connex_job_id):
        if not product_code or not connex_job_id:
            return
        data = {'material': product_code}
        material = self._send_connex_get_material(product_code)
        if not material:
            job_material = self._send_connex_create_material(product_code)
        self._send_connex_update_job(data=data, connex_job_id=connex_job_id)

    def _send_connex_get_material(self, product_code):
        try:
            client = self._context.get("client")
            res = client._connex_get_material({'name': product_code})
        except Exception as error:
            if type(error).__name__ == "MissingError":
                # 1
                res = {}
            else:
                res = None
                raise UserError(_(
                    u"Failed to get material details"
                ))
        return res

    def _send_connex_create_material(self, product_code):
        if not product_code:
            return []
        data = {
            'name': product_code
        }
        try:
            client = self._context.get("client")
            res = client._connex_create_material(data)

        except Exception as error:
            if type(error).__name__ == "MissingError":
                # 1
                res = {}
            else:
                res = None
                raise UserError(_(
                    u"Failed to get material details"
                ))
        return res

    def _get_connex_production(self):
        if not self._context.get("client", False):
            self = self._initiate_client_context()
        try:
            client = self._context.get("client")
            res = client._connex_get_new_production()
        except Exception as error:
            if type(error).__name__ == "MissingError":
                # 1
                res = {}
            else:
                res = None
                raise UserError(_(
                    u"Failed to get production details"
                ))
        return res

    def _set_process_connex_production(self, data):
        if not self._context.get("client", False):
            self = self._initiate_client_context()
        try:
            client = self._context.get("client")
            res = client._connex_set_process_production(data)
        except Exception as error:
            if type(error).__name__ == "MissingError":
                # 1
                res = {}
            else:
                res = None
                raise UserError(_(
                    u"Failed to set production details"
                ))
        return res

    def _initiate_client_context(self):
        ctx = self._context.copy()
        new_ctx = self._return_client_context()
        ctx.update(new_ctx)
        return self.with_context(ctx)

    @api.model
    def _return_client_context(self):
        """
        The method to return necessary to client context (like session, root directory, etc.)

        Returns:
         * dict
        """
        Config = self.env['ir.config_parameter'].sudo()
        with_context = {}
        connex_url = Config.get_param('connex_url', '')
        connex_user = Config.get_param('connex_user', '')
        connex_password = Config.get_param('connex_password', '')
        client = Client(connex_url, connex_user, connex_password)
        if client:
            with_context.update({"client": client, })
        else:
            mes = u"Connex Services are not available"
            raise UserError(mes)
        return with_context
