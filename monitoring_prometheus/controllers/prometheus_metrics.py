# Copyright 2016-2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from prometheus_client import generate_latest

from odoo.http import Controller, route

from ..models.psutils_helpers import get_process_info


class PrometheusController(Controller):
    @route("/metrics", auth="public")
    def metrics(self):
        get_process_info()
        return generate_latest()
