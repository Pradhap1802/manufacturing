# -*- coding: utf-8 -*-
from odoo import models, fields

class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    production_id = fields.Many2one('mrp.production', string='Manufacturing Order', copy=False)
    workorder_id = fields.Many2one('mrp.workorder', string='Work Order', copy=False)
    