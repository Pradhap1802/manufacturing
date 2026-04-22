# -*- coding: utf-8 -*-
from odoo import models, fields, api

class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    employee_cost_ids = fields.One2many(
        'mrp.workcenter.employee', 'workcenter_id', string='Labour Cost/Hour',
        help="Employees allowed to work at this work center and their costs.")

    # Keeping this as a computed field for compatibility with existing logic if needed
    allowed_employee_ids = fields.Many2many(
        'hr.employee', string='Allowed Employees',
        compute='_compute_allowed_employee_ids', store=True)

    @api.depends('employee_cost_ids.employee_id')
    def _compute_allowed_employee_ids(self):
        for wc in self:
            wc.allowed_employee_ids = wc.employee_cost_ids.mapped('employee_id')

class MrpWorkcenterEmployee(models.Model):
    _name = 'mrp.workcenter.employee'
    _description = 'Work Center Employee'

    workcenter_id = fields.Many2one('mrp.workcenter', string='Work Center', required=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    cost_hour = fields.Float(string='Cost per Hour', help="Calculated based on employee's hourly cost.")

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.cost_hour = self.employee_id.hourly_cost

class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    allowed_employee_ids = fields.Many2many(
        'hr.employee', string='Allowed Employees',
        help="Employees allowed to perform this operation.")
