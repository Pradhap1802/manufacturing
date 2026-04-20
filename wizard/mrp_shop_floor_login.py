# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MrpShopFloorLogin(models.TransientModel):
    _name = 'mrp.shop.floor.login'
    _description = 'Shop Floor Login'

    pin = fields.Char(string='Employee PIN', required=True)

    def action_login(self):
        self.ensure_one()
        employee = self.env['hr.employee'].search([('pin', '=', self.pin)], limit=1)
        if not employee:
            raise UserError(_("Invalid PIN. Please try again."))

        # Return the shop floor action with extra context/domain
        action = self.env.ref('manufacturing.action_mrp_shop_floor').read()[0]
        
        # Determine which operations are allowed for this employee
        # This includes work centers where they are allowed and operations where they are specifically allowed
        allowed_workcenter_ids = self.env['mrp.workcenter'].search([
            ('allowed_employee_ids', 'in', employee.id)
        ]).ids
        
        allowed_operation_ids = self.env['mrp.routing.workcenter'].search([
            ('allowed_employee_ids', 'in', employee.id)
        ]).ids

        # Build the domain: 
        # (WorkCenter is in allowed list) OR (Specific Operation is in allowed list)
        domain = [
            ('state', 'in', ('ready', 'progress')),
            '|',
            ('workcenter_id', 'in', allowed_workcenter_ids),
            ('operation_id', 'in', allowed_operation_ids)
        ]
        
        action['domain'] = domain
        action['context'] = {
            'default_employee_id': employee.id,
            'authenticated_employee_id': employee.id,
            'search_default_ready': 1
        }
        action['name'] = _("Shop Floor - %s") % employee.name
        return action
