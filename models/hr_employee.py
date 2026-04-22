# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    hourly_cost = fields.Float('Hourly Cost', default=0.0, help="Labor cost per hour for manufacturing operations")

    def action_open_mrp_shop_floor_login(self):
        self.ensure_one()
        return {
            'name': _('Employee Login'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.shop.floor.login',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_employee_id': self.id,
            }
        }
    def write(self, vals):
        res = super(HrEmployee, self).write(vals)
        if 'hourly_cost' in vals:
            # Sync to workcenter employee records to keep costs aligned
            self.env['mrp.workcenter.employee'].search([('employee_id', 'in', self.ids)]).write({
                'cost_hour': vals['hourly_cost']
            })
        return res

class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    hourly_cost = fields.Float(readonly=True, help="Exposed for manufacturing costing background processes")
