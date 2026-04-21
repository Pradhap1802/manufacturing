# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    employee_id = fields.Many2one('hr.employee', string='Employee', copy=False)

    def action_open_shop_floor_wizard(self):
        self.ensure_one()
        return {
            'name': _('Shop Floor Interaction'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.shop.floor.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_workorder_id': self.id,
                'default_employee_id': self.env.context.get('authenticated_employee_id') or self.employee_id.id,
            }
        }

    def action_open_pause_wizard(self):
        """Open the wizard in pause context — shows timer and qty info before pausing."""
        self.ensure_one()
        return {
            'name': _('Pause Work Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.shop.floor.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_workorder_id': self.id,
                'default_employee_id': self.env.context.get('authenticated_employee_id') or self.employee_id.id,
                'shop_floor_mode': 'pause',
            }
        }

    def action_open_finish_wizard(self):
        """Open the wizard in finish context — shows qty producing and scrap entry."""
        self.ensure_one()
        return {
            'name': _('Finish Work Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.shop.floor.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_workorder_id': self.id,
                'default_employee_id': self.env.context.get('authenticated_employee_id') or self.employee_id.id,
                'shop_floor_mode': 'finish',
            }
        }

    def _cal_cost(self, date=False):
        """Override to use employee-specific costs if available, mimicking Enterprise."""
        total = 0
        for workorder in self:
            # Aggregate from our custom productivity timer field 'total_cost'
            timers = workorder.time_ids.filtered(lambda t: t.date_end and (not date or t.date_end < date))
            total += sum(timers.mapped('total_cost'))
        return total

    def button_start(self):

        self.ensure_one()
        # If no employee is set, we use the logged-in user's employee
        if not self.employee_id:
            employee = self.env.user.employee_id
            if employee:
                self.employee_id = employee
            else:
                raise UserError(_("Please set an employee before starting the work order."))
        
        # Check if employee is allowed
        allowed_ids = self.workcenter_id.allowed_employee_ids.ids
        if allowed_ids and self.employee_id.id not in allowed_ids:
            raise UserError(_("Employee %s is not allowed to work at work center %s.") % (self.employee_id.name, self.workcenter_id.name))
        
        # Check operation level allowed employees if any
        operation_allowed_ids = self.operation_id.allowed_employee_ids.ids
        if operation_allowed_ids and self.employee_id.id not in operation_allowed_ids:
            raise UserError(_("Employee %s is not allowed to perform operation %s.") % (self.employee_id.name, self.operation_id.name))

        return super(MrpWorkorder, self).button_start()

    def button_finish(self):
        res = super(MrpWorkorder, self).button_finish()
        # Optionally clear employee or keep for history
        return res

    def action_shop_floor_maintenance(self):
        self.ensure_one()
        return {
            'name': _('Create Maintenance Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'maintenance.request',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_maintenance_type': 'corrective',
                'default_equipment_id': self.workcenter_id.equipment_ids[:1].id if self.workcenter_id.equipment_ids else False,
                'default_description': _('Maintenance for work order %s at work center %s') % (self.name, self.workcenter_id.name),
            }
        }

    def action_shop_floor_quality_alert(self):
        self.ensure_one()
        return {
            'name': _('Create Quality Alert'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.quality.alert',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_workorder_id': self.id,
                'default_product_id': self.product_id.id,
                'default_production_id': self.production_id.id,
            }
        }

class MrpQualityAlert(models.Model):
    _name = 'mrp.quality.alert'
    _description = 'MRP Quality Alert'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    workorder_id = fields.Many2one('mrp.workorder', 'Work Order')
    product_id = fields.Many2one('product.product', 'Product')
    production_id = fields.Many2one('mrp.production', 'Production Order')
    description = fields.Text('Description')
    user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user)
    priority = fields.Selection([('0', 'Normal'), ('1', 'Low'), ('2', 'High'), ('3', 'Very High')], string='Priority', default='1')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('mrp.quality.alert') or _('New')
        return super(MrpQualityAlert, self).create(vals_list)
