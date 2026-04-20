# -*- coding: utf-8 -*-
from odoo import models, fields, _

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
