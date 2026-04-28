# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, date

class MrpWorkcenterProductivity(models.Model):
    _inherit = 'mrp.workcenter.productivity'

    employee_id = fields.Many2one('hr.employee', string='Operator')
    total_cost = fields.Float('Total Cost', compute='_compute_total_cost', store=True)

    # Downtime tracking
    downtime_reason = fields.Selection([
        ('breakdown',   'Machine Breakdown'),
        ('material',    'Material Shortage'),
        ('quality',     'Quality Hold'),
        ('maintenance', 'Planned Maintenance'),
        ('operator',    'Operator Absent'),
        ('changeover',  'Product Changeover'),
        ('other',       'Other'),
    ], string='Downtime Reason')
    downtime_notes = fields.Text('Downtime Notes')

    def _compute_total_cost(self):
        for time in self:
            duration = time.duration / 60.0  # Duration is in minutes
            employee = time.employee_id.sudo()
            rate = employee.hourly_cost if employee else time.workcenter_id.costs_hour
            time.total_cost = duration * rate


