# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MrpShopFloorLogin(models.TransientModel):
    _name = 'mrp.shop.floor.login'
    _description = 'Shop Floor Login'

    employee_id = fields.Many2one('hr.employee', string='Operator', required=True)
    employee_ids = fields.Many2many('hr.employee', string='Available Operators', compute='_compute_employee_ids')
    pin = fields.Char(string='Employee PIN', required=True)

    @api.depends('pin')
    def _compute_employee_ids(self):
        # Provide all internal employees for the selection board
        employees = self.env['hr.employee'].search([('active', '=', True)])
        for record in self:
            record.employee_ids = [(6, 0, employees.ids)]

    def action_login(self):
        self.ensure_one()
        # Secure PIN check against the selected employee
        if not self.employee_id.sudo().pin or self.employee_id.sudo().pin != self.pin:
            raise UserError(_("Invalid PIN for %s. Please try again.") % self.employee_id.name)

        employee = self.employee_id
        
        # Return the shop floor action with extra context/domain
        action = self.env.ref('manufacturing.action_mrp_shop_floor').sudo().read()[0]
        
        # Determine which operations/work centers are allowed for this employee
        allowed_workcenter_ids = self.env['mrp.workcenter'].search([
            ('allowed_employee_ids', 'in', employee.id)
        ]).ids
        
        allowed_operation_ids = self.env['mrp.routing.workcenter'].search([
            ('allowed_employee_ids', 'in', employee.id)
        ]).ids

        # Build the domain for Work Orders specific to THIS operator
        # They see work orders in their allowed work centers/operations
        domain = [
            ('state', 'in', ('ready', 'progress', 'pending')),
            '|',
            ('workcenter_id', 'in', allowed_workcenter_ids),
            ('operation_id', 'in', allowed_operation_ids)
        ]
        
        action['domain'] = domain
        action['context'] = {
            'default_employee_id': employee.id,
            'authenticated_employee_id': employee.id,
            'search_default_ready': 1,
            'search_default_employee_id': employee.id,
        }
        action['name'] = _("Shop Floor - %s") % employee.name
        action['target'] = 'fullscreen'
        return action
