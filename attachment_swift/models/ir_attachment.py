# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


import base64
import logging
import os
from ..swift_uri import SwiftUri

from odoo import api, exceptions, models, _

_logger = logging.getLogger(__name__)

try:
    import swiftclient
    from swiftclient.exceptions import ClientException
except ImportError:
    swiftclient = None
    ClientException = None
    _logger.debug("Cannot 'import swiftclient'.")


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    store_name = 'swift'

    @api.model
    def _get_swift_connection(self):
        """ Returns a connection object for the Swift object store """
        host = os.environ.get('SWIFT_HOST')
        account = os.environ.get('SWIFT_ACCOUNT')
        password = os.environ.get('SWIFT_PASSWORD')
        if not (host and account and password):
            raise exceptions.UserError(_(
                '''Problem connecting to Swift store, are the env variables
                   (SWIFT_HOST, SWIFT_ACCOUNT, SWIFT_PASSWORD) properly set ?
                '''))
        try:
            conn = swiftclient.client.Connection(authurl=host,
                                                 user=account,
                                                 key=password)
        except ClientException:
            _logger.exception('Error connecting to Swift object store')
            raise exceptions.UserError(_('Error on Swift connection'))
        return conn

    @api.model
    def _store_file_read(self, fname, bin_size=False):
        if fname.startswith('swift://'):
            swifturi = SwiftUri(fname)
            conn = self._get_swift_connection()
            try:
                resp, obj_content = conn.get_object(swifturi.container(),
                                                    swifturi.item())
                read = base64.b64encode(obj_content)
            except ClientException:
                _logger.exception(
                    'Error reading object from Swift object store')
                raise exceptions.UserError(_('Error reading on Swift'))
            return read
        else:
            return super(IrAttachment, self)._store_file_read(fname, bin_size)

    def _store_file_write(self, value, checksum):
        if self._storage() == self.store_name:
            container = os.environ.get('SWIFT_WRITE_CONTAINER')
            conn = self._get_swift_connection()
            conn.put_container(container)
            bin_data = value.decode('base64')
            key = self._compute_checksum(bin_data)
            filename = 'swift://{}/{}'.format(container, key)
            try:
                conn.put_object(container, key, bin_data)
            except ClientException:
                _logger.exception('Error connecting to Swift object store')
                raise exceptions.UserError(_('Error writting to Swift'))
        else:
            _super = super(IrAttachment, self)
            filename = _super._store_file_write(value, checksum)
        return filename

    @api.model
    def _file_delete_from_store(self, fname):
        if fname.startswith('swift://'):
            swifturi = SwiftUri(fname)
            container = swifturi.container()
            if container == os.environ.get('SWIFT_WRITE_CONTAINER'):
                conn = self._get_swift_connection()
                try:
                    conn.delete_object(container, swifturi.item())
                except ClientException:
                    _logger.exception(
                        _('Error deleting an object on the Swift store'))
                    raise exceptions.UserError(_('Error deleting on Swift'))
        else:
            super(IrAttachment, self)._file_delete(fname)

    def _get_stores(self):
        l = [self.store_name]
        l += super(IrAttachment, self)._get_stores()
        return l
