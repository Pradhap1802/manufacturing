# -*- coding: utf-8 -*-
from odoo import models, fields, api

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    quality_check_ids = fields.One2many('quality.check.custom', 'production_id', string='Quality Checks')
    quality_alert_ids = fields.One2many('quality.alert.custom', 'production_id', string='Quality Alerts')
    quality_alert_count = fields.Integer(compute='_compute_quality_alert_count')

    @api.depends('quality_alert_ids')
    def _compute_quality_alert_count(self):
        for production in self:
            production.quality_alert_count = len(production.quality_alert_ids)

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    quality_check_ids = fields.One2many('quality.check.custom', 'workorder_id', string='Quality Checks')
    quality_alert_ids = fields.One2many('quality.alert.custom', 'workorder_id', string='Quality Alerts')
    rejection_qty = fields.Float('Rejection Qty', default=0.0)
    rejection_reason_id = fields.Many2one('quality.rejection.reason', string='Rejection Reason')

class QualityRejectionReason(models.Model):
    _name = 'quality.rejection.reason'
    _description = 'Quality Rejection Reason'

    name = fields.Char('Reason', required=True)
    description = fields.Text('Description')
