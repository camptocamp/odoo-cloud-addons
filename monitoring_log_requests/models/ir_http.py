# -*- coding: utf-8 -*-
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import json
import logging
import time

from openerp import models
from openerp.http import request as http_request
from openerp.tools.config import config


_logger = logging.getLogger(u'monitoring.http.requests')


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def _dispatch(self):
        begin = time.time()
        response = super(IrHttp, self)._dispatch()
        end = time.time()
        if (not self._monitoring_blacklist(http_request) and
                self._monitoring_filter(http_request)):
            info = self._monitoring_info(http_request, response, begin, end)
            self._monitoring_log(info)
        return response

    def _monitoring_blacklist(self, request):
        path_info = request.httprequest.environ.get(u'PATH_INFO')
        if path_info.startswith(u'/longpolling/'):
            return True
        return False

    def _monitoring_filter(self, request):
        return True

    def _monitoring_info(self, request, response, begin, end):
        path = request.httprequest.environ.get(u'PATH_INFO')
        info = {
            # timing
            'start_time': time.strftime("%Y-%m-%d %H:%M:%S",
                                        time.gmtime(begin)),
            'duration': end - begin,
            # HTTP things
            'method': request.httprequest.method,
            'url': request.httprequest.url,
            'path': path,
            'content_type': request.httprequest.environ.get('CONTENT_TYPE'),
            'user_agent': request.httprequest.environ.get('HTTP_USER_AGENT'),
            # Odoo things
            'db': None,
            'uid': request.uid,
            'login': None,
            'server_environment': config.get('running_env'),
            'model': None,
            'model_method': None,
            'workflow_signal': None,
            # response things
            'response_status_code': None,
        }
        if hasattr(request, 'status_code'):
            info['status_code'] = response.status_code
        if hasattr(request, 'session'):
            info.update({
                'login': request.session.get('login'),
                'db': request.session.get('db'),
            })
        if hasattr(request, 'params'):
            info.update({
                'model': request.params.get('model'),
                'model_method': request.params.get('method'),
                'workflow_signal': request.params.get('signal'),
            })
        return info

    def _monitoring_log(self, info):
        _logger.info(json.dumps(info))
