# -*- coding: utf-8 -*-

import logging
import requests
import pprint
import werkzeug
from werkzeug.urls import url_encode

from odoo import fields, _
from odoo.exceptions import UserError, MissingError

_logger = logging.getLogger(__name__)


class ConnexApiClient():
    TIMEOUT = 60

    def __init__(self, connex_url, connex_user, connex_password):
        """
        Init method
        """
        self.connex_url = connex_url
        self.connex_user = connex_user
        self.connex_password = connex_password
        self.session = False

    def _connex_login(self):
        """
        The method to return authorization response

        Returns:
         * response
        """
        header = {
            "Content-Type": "application/json",
        }
        self.session = requests.Session()
        data = {
            "username": self.connex_user,
            "password": self.connex_password,
        }
        url = "/login"
        _logger.info("Connect Connex Login")
        res = self._request_connex(method="POST", url=url, data=data, headers=header)
        response = res and res.json() or False
        return response

    def _connex_create_job(self, data):
        """
            The method to return authorization response

            Returns:
             * response
        """
        header = {
            "Content-Type": "text/plain",
        }
        if not self.session:
            self._connex_login()
        url = "/data/job"
        res = self._request_connex(method="PUT", url=url, data=data, headers=header)
        response = res and res.json() or False
        return response

    def _connex_get_job(self, job_id):
        """
            The method to return authorization response

            Returns:
             * response
        """
        header = {
            "Content-Type": "application/json",
        }
        if not self.session:
            self._connex_login()
        res = self._request_connex(method="GET", url=f'/data/job/{job_id}', headers=header)
        response = res and res.json() or False
        return response

    def _connex_create_batch(self, data):
        """
            The method to return authorization response

            Returns:
             * response
        """
        header = {
            "Content-Type": "text/plain",
        }
        if not self.session:
            self._connex_login()
        url = "/data/batch"
        res = self._request_connex(method="PUT", url=url, data=data, headers=header)
        response = res and res.json() or False
        return response

    def _connex_create_part(self, data):
        """
            The method to return authorization response

            Returns:
             * response
        """
        header = {
            "Content-Type": "text/plain",
        }
        if not self.session:
            self._connex_login()
        url = "/data/part"
        res = self._request_connex(method="PUT", url=url, data=data, headers=header)
        response = res and res.json() or False
        return response

    def _connex_update_job(self, data, job_id):
        """
            The method to return authorization response

            Returns:
             * response
        """
        header = {
            "Content-Type": "application/json",
        }
        if not self.session:
            self._connex_login()
        res = self._request_connex(method="PUT", url=f'/data/job/{job_id}', data=data, headers=header)
        response = res and res.json() or False
        return response

    def _connex_get_part(self, part_id):
        """
            The method to return authorization response

            Returns:
             * response
        """
        header = {
            "Content-Type": "application/json",
        }
        if not self.session:
            self._connex_login()
        res = self._request_connex(method="GET", url=f'/data/part/{part_id}', headers=header)
        response = res and res.json() or False
        return response

    def _connex_get_profile(self, params):
        """
            The method to return authorization response

            Returns:
             * response
        """
        header = {
            "Content-Type": "application/json",
        }
        if not self.session:
            self._connex_login()
        res = self._request_connex(method="GET", url=f'/data/profile?%s' % url_encode(params), headers=header)
        response = res and res.json() or False
        return response

    def _connex_create_profile(self, data):
        """
            The method to return authorization response

            Returns:
             * response
        """
        header = {
            "Content-Type": "text/plain",
        }
        if not self.session:
            self._connex_login()
        url = "/data/profile"
        res = self._request_connex(method="PUT", url=url, data=data, headers=header)
        response = res and res.json() or False
        return response

    def _connex_get_material(self, params):
        """
            The method to return authorization response

            Returns:
             * response
        """
        header = {
            "Content-Type": "application/json",
        }
        if not self.session:
            self._connex_login()
        res = self._request_connex(method="GET", url=f'/data/material?%s' % url_encode(params), headers=header)
        response = res and res.json() or False
        return response

    def _connex_create_material(self, data):
        """
            The method to return authorization response

            Returns:
             * response
        """
        header = {
            "Content-Type": "text/plain",
        }
        if not self.session:
            self._connex_login()
        url = "/data/material"
        res = self._request_connex(method="PUT", url=url, data=data, headers=header)
        response = res and res.json() or False
        return response

    def _connex_create_operation(self, data):
        """
            The method to return authorization response

            Returns:
             * response
        """
        header = {
            "Content-Type": "text/plain",
        }
        if not self.session:
            self._connex_login()
        url = "/data/operation"
        res = self._request_connex(method="PUT", url=url, data=data, headers=header)
        response = res and res.json() or False
        return response

    def _connex_get_machine(self, params):
        """
            The method to return authorization response

            Returns:
             * response
        """
        header = {
            "Content-Type": "application/json",
        }
        if not self.session:
            self._connex_login()
        res = self._request_connex(method="GET", url=f'/data/machine?%s' % url_encode(params), headers=header)
        response = res and res.json() or False
        return response

    def _connex_create_machine(self, data):
        """
            The method to return authorization response

            Returns:
             * response
        """
        header = {
            "Content-Type": "text/plain",
        }
        if not self.session:
            self._connex_login()
        url = "/data/machine"
        res = self._request_connex(method="PUT", url=url, data=data, headers=header)
        response = res and res.json() or False
        return response

    def _connex_create_machine_profile(self, data):
        """
            The method to return authorization response

            Returns:
             * response
        """
        header = {
            "Content-Type": "text/plain",
        }
        if not self.session:
            self._connex_login()
        url = "/data/machine_profile"
        res = self._request_connex(method="PUT", url=url, data=data, headers=header)
        response = res and res.json() or False
        return response

    def _connex_get_machine_profile(self, params):
        """
            The method to return authorization response

            Returns:
             * response
        """
        header = {
            "Content-Type": "application/json",
        }
        if not self.session:
            self._connex_login()
        res = self._request_connex(method="GET", url=f'/data/machine_profile?%s' % url_encode(params), headers=header)
        response = res and res.json() or False
        return response

    def _connex_get_new_production(self):
        """
            The method to return authorization response

            Returns:
             * response
        """
        header = {
            "Content-Type": "application/json",
        }
        if not self.session:
            self._connex_login()
        res = self._request_connex(method="GET", url=f'/get_new_production', headers=header)
        response = res and res.json() or False
        return response

    def _connex_set_process_production(self, data):
        """
            The method to return authorization response

            Returns:
             * response
        """
        header = {
            "Content-Type": "application/json",
        }
        if not self.session:
            self._connex_login()
        res = self._request_connex(method="PUT", url="/set_processed", data=data, headers=header)
        response = res and res.json() or False
        return response

    def _request_connex(self, method, url, params={}, data={}, headers={}, **kwargs):
        """
        The method to execute request for Connex API

        Args:
         * method - REST API method for request
         * url - definite method of REST API (without API url)
         * params - dict of encoded request parameters
         * data - string
         * headers - request headers

        Returns:
         * response
        """
        _headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
        }
        headers.update(_headers)
        r_url = self.connex_url + url
        if method.upper() in ('GET', 'DELETE'):
            res = self.session.request(
                method,
                r_url,
                params=params,
                timeout=self.TIMEOUT,
                headers=headers,
            )
        elif method.upper() in ('POST', 'PATCH', 'PUT'):
            res = self.session.request(
                method,
                r_url,
                params=params,
                json=data,
                headers=headers,
                timeout=self.TIMEOUT,
            )
        else:
            raise Exception(_(u'Method not supported {} not in [GET, POST, PUT, PATCH or DELETE]!'.format(method)))

        if res.status_code in (200, 201, 202):
            _logger.info("Connex Response response: {}".format(pprint.pformat(res.json())))
            return res
        elif res.status_code == 404:
            raise UserError(_("The Requested URL is not Found"))
        elif res.status_code == 204:
            raise MissingError(res.json())
        else:
            raise UserError(res.json())
