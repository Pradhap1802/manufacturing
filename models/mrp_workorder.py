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
                'default_wizard_mode': 'pause',
            }
        }

    def action_open_resume_wizard(self):
        """Open the wizard to update qty_producing before resuming."""
        self.ensure_one()
        return {
            'name': _('Resume Work Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.shop.floor.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_workorder_id': self.id,
                'default_employee_id': self.env.context.get('authenticated_employee_id') or self.employee_id.id,
                'default_wizard_mode': 'resume',
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
                'default_wizard_mode': 'finish',
            }
        }

    def action_exit_shop_floor(self):
        """Exit the Shop Floor fullscreen mode and return to Manufacturing Orders."""
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("mrp.mrp_production_action")
        # Removing fullscreen target just in case, ensuring normal UI loads
        action['target'] = 'current'
        return action


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
        equipment_id = False
        # Defensively check for Enterprise equipment field to avoid AttributeError
        if hasattr(self.workcenter_id, 'equipment_ids') and self.workcenter_id.equipment_ids:
            equipment_id = self.workcenter_id.equipment_ids[:1].id
            
        return {
            'name': _('Create Maintenance Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'maintenance.request',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_maintenance_type': 'corrective',
                'default_equipment_id': equipment_id,
                'default_description': _('Maintenance for work order %s at work center %s') % (self.name, self.workcenter_id.name),
            }
        }

    def action_shop_floor_quality_alert(self):
        self.ensure_one()
        # Verify if Enterprise Quality module is installed, otherwise use our robust custom one
        if 'quality.alert' in self.env:
             return {
                'name': _('Create Quality Alert'),
                'type': 'ir.actions.act_window',
                'res_model': 'quality.alert',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_production_id': self.production_id.id,
                    'default_workorder_id': self.id,
                    'default_product_id': self.product_id.id,
                }
            }
        
        # Determine the first stage of our custom quality alert
        first_stage = self.env['mrp.quality.alert.stage'].search([], limit=1)
        
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
                'default_stage_id': first_stage.id if first_stage else False,
            }
        }

    def action_shop_floor_scrap(self):
        self.ensure_one()
        return {
            'name': _('Scrap'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.scrap',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_workorder_id': self.id,
                'default_production_id': self.production_id.id,
                'default_product_id': self.product_id.id,
                'default_uom_id': self.product_uom_id.id,
                'default_company_id': self.company_id.id,
                'default_location_id': self.production_id.location_src_id.id,
            }
        }

class MrpQualityReason(models.Model):
    _name = 'mrp.quality.reason'
    _description = 'Root Cause Reason'

    name = fields.Char('Reason', required=True)

class MrpQualityAlertStage(models.Model):
    _name = 'mrp.quality.alert.stage'
    _description = 'Quality Alert Stage'
    _order = 'sequence, id'

    name = fields.Char('Stage Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=10)
    folded = fields.Boolean('Folded in Kanban')

class MrpQualityAlert(models.Model):
    _name = 'mrp.quality.alert'
    _description = 'MRP Quality Alert'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    workorder_id = fields.Many2one('mrp.workorder', 'Work Order')
    product_id = fields.Many2one('product.product', 'Product')
    production_id = fields.Many2one('mrp.production', 'Production Order', related='workorder_id.production_id', store=True)
    workcenter_id = fields.Many2one('mrp.workcenter', 'Work Center', related='workorder_id.workcenter_id', store=True)
    operation_id = fields.Many2one('mrp.routing.workcenter', 'Operation', related='workorder_id.operation_id', store=True)
    
    description = fields.Text('Description')
    action_corrective = fields.Text('Corrective Action')
    action_preventive = fields.Text('Preventive Action')
    
    user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user, tracking=True)
    date_alert = fields.Datetime('Alert Date', default=fields.Datetime.now, readonly=True)
    date_close = fields.Datetime('Date Closed', readonly=True)
    priority = fields.Selection([('0', 'Normal'), ('1', 'Low'), ('2', 'High'), ('3', 'Very High')], string='Priority', default='1', tracking=True)
    
    reason_id = fields.Many2one('mrp.quality.reason', string='Root Cause')
    stage_id = fields.Many2one('mrp.quality.alert.stage', string='Stage', ondelete='set null', tracking=True, index=True, copy=False)
    
    # Quality Measures (Enterprise Style)
    test_type = fields.Selection([
        ('pass_fail', 'Pass/Fail'),
        ('measure', 'Measure'),
        ('picture', 'Take a Picture')
    ], string='Test Type', default='pass_fail', tracking=True)

    test_result = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail')
    ], string='Test Result', tracking=True)

    measure = fields.Float('Measurement', tracking=True)
    picture = fields.Binary('Picture', attachment=True)

    def action_see_workorder(self):
        self.ensure_one()
        return {
            'name': _('Work Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.workorder',
            'view_mode': 'form',
            'res_id': self.workorder_id.id,
            'target': 'current',
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('mrp.quality.alert') or _('New')
            if not vals.get('stage_id'):
                vals['stage_id'] = self.env['mrp.quality.alert.stage'].search([], limit=1).id
        return super(MrpQualityAlert, self).create(vals_list)
