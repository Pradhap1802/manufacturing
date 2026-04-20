# -*- coding: utf-8 -*-
from odoo import models, fields

class MrpWorkcenterProductivity(models.Model):
    _inherit = 'mrp.workcenter.productivity'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    total_cost = fields.Float('Total Cost', compute='_compute_total_cost', store=True)

    def _compute_total_cost(self):
        for time in self:
            duration = time.duration / 60.0  # Duration is in minutes
            rate = time.employee_id.hourly_cost if time.employee_id else time.workcenter_id.costs_hour
            time.total_cost = duration * rate
