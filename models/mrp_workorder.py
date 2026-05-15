# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    employee_id = fields.Many2one('hr.employee', string='Employee', copy=False)
    
    # Subcontracting Fields
    is_subcontracted = fields.Boolean(related='operation_id.is_subcontracted', store=True, readonly=True)
    vendor_id = fields.Many2one('res.partner', related='operation_id.vendor_id', store=True, readonly=True)
    delivery_picking_id = fields.Many2one('stock.picking', string='Send to Subcontractor', copy=False, readonly=True)
    receipt_picking_id = fields.Many2one('stock.picking', string='Receive from Subcontractor', copy=False, readonly=True)

    # Operations Tracking Fields
    operation_type = fields.Selection([
        ('inhouse', 'In-house'),
        ('subcontract', 'Subcontract')
    ], string='Operation Type', compute='_compute_operation_type', store=True)
    
    qty_sent = fields.Float('Qty Sent', compute='_compute_subcontract_qtys', store=True)
    qty_received = fields.Float('Qty Received', compute='_compute_subcontract_qtys', store=True)
    rejected_qty = fields.Float('Rejected Qty')
    remarks = fields.Char('Remarks')
    
    tracking_status = fields.Selection([
        ('pending', 'Pending'),
        ('ready', 'Ready'),
        ('progress', 'In Progress'),
        ('sent', 'Sent to Vendor'),
        ('received', 'Received'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', compute='_compute_tracking_status', store=True)

    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    operation_cost = fields.Monetary('Cost', compute='_compute_operation_cost', store=True, readonly=False, currency_field='company_currency_id')

    is_first_started_wo = fields.Boolean('Is First Started WO', compute='_compute_is_last_unfinished_wo')
    is_last_unfinished_wo = fields.Boolean('Is Last Unfinished WO', compute='_compute_is_last_unfinished_wo')

    @api.depends('production_id.workorder_ids')
    def _compute_is_last_unfinished_wo(self):
        for wo in self:
            wo.is_first_started_wo = all(w.state != 'done' for w in (wo.production_id.workorder_ids - wo))
            other_wos = wo.production_id.workorder_ids - wo
            other_states = other_wos.mapped(lambda w: w.state in ['done', 'cancel'])
            wo.is_last_unfinished_wo = all(other_states)

    @api.depends('is_subcontracted')
    def _compute_operation_type(self):
        for wo in self:
            wo.operation_type = 'subcontract' if wo.is_subcontracted else 'inhouse'

    @api.depends('delivery_picking_id.state', 'receipt_picking_id.state', 'delivery_picking_id.move_ids', 'receipt_picking_id.move_ids')
    def _compute_subcontract_qtys(self):
        for wo in self:
            qty_sent = 0.0
            qty_rec = 0.0
            if wo.delivery_picking_id and wo.delivery_picking_id.state == 'done':
                for move in wo.delivery_picking_id.move_ids:
                    qty_sent += move.quantity
            if wo.receipt_picking_id and wo.receipt_picking_id.state == 'done':
                for move in wo.receipt_picking_id.move_ids:
                    qty_rec += move.quantity
            wo.qty_sent = qty_sent
            wo.qty_received = qty_rec

    @api.depends('state', 'is_subcontracted', 'delivery_picking_id.state', 'receipt_picking_id.state')
    def _compute_tracking_status(self):
        for wo in self:
            if wo.state == 'cancel':
                wo.tracking_status = 'cancel'
                continue
            if wo.state == 'done':
                wo.tracking_status = 'done'
                continue
            
            if wo.is_subcontracted:
                if wo.receipt_picking_id and wo.receipt_picking_id.state == 'done':
                    wo.tracking_status = 'received'
                elif wo.delivery_picking_id and wo.delivery_picking_id.state == 'done':
                    wo.tracking_status = 'sent'
                elif wo.delivery_picking_id:
                    wo.tracking_status = 'ready' # Waiting for delivery validation
                elif wo.state == 'progress':
                    wo.tracking_status = 'progress'
                elif wo.state == 'ready':
                    wo.tracking_status = 'ready'
                elif wo.state == 'pending':
                    wo.tracking_status = 'pending'
                else:
                    wo.tracking_status = 'pending'
            else:
                if wo.state == 'progress':
                    wo.tracking_status = 'progress'
                elif wo.state == 'ready':
                    wo.tracking_status = 'ready'
                elif wo.state == 'pending':
                    wo.tracking_status = 'pending'
                else:
                    wo.tracking_status = 'pending'

    @api.depends('time_ids.total_cost')
    def _compute_operation_cost(self):
        for wo in self:
            wo.operation_cost = sum(wo.time_ids.mapped('total_cost'))

    def action_open_delivery_picking(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': self.delivery_picking_id.id,
            'target': 'current',
        }

    def action_open_receipt_picking(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': self.receipt_picking_id.id,
            'target': 'current',
        }

    def action_send_to_vendor(self):
        self.ensure_one()
        if self.delivery_picking_id:
            raise UserError(_("Delivery to vendor already created!"))
            
        return {
            'name': _('Send to Subcontractor'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.subcontracting.delivery.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_workorder_id': self.id,
            }
        }

    def action_receive_from_vendor(self):
        self.ensure_one()
        if not self.delivery_picking_id or self.delivery_picking_id.state != 'done':
            raise UserError(_("You must send the items to the vendor before receiving them."))
            
        return {
            'name': _('Receive from Subcontractor'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.subcontracting.receive.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_workorder_id': self.id,
                'default_qty_received': self.qty_production,
                'default_cost': 0.0,
            }
        }

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

        # Enforce Sequential Logic
        if self.state == 'pending':
            raise UserError(_("Sequential Logic Enforced: You cannot start this operation until the previous operation is completed."))

        # If no employee is set, we use the authenticated employee from context or logged-in user's employee
        if not self.employee_id:
            auth_emp_id = self.env.context.get('authenticated_employee_id')
            if auth_emp_id:
                employee = self.env['hr.employee'].browse(auth_emp_id)
            else:
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

        res = super(MrpWorkorder, self).button_start()
        # Find the active timer just created and assign the employee
        active_timer = self.time_ids.filtered(lambda t: not t.date_end)
        if active_timer:
            active_timer.write({'employee_id': self.employee_id.id})
        return res

    def button_finish(self):
        res = super(MrpWorkorder, self).button_finish()
        # Optionally clear employee or keep for history
        return res

    def pre_record_production(self):
        self.ensure_one()
        self.production_id._check_company()
        if float_compare(self.qty_producing, 0, precision_rounding=self.product_uom_id.rounding) <= 0:
            raise UserError(_('Please set the quantity you are currently producing. It should be different from zero.'))

    def record_production(self):
        if not self:
            return True

        self.pre_record_production()

        backorder = False
        # Trigger the backorder process if we produce less than expected
        if float_compare(self.qty_producing, self.qty_remaining, precision_rounding=self.product_uom_id.rounding) == -1 and self.is_first_started_wo:
            if self.production_id.picking_type_id.create_backorder == 'ask':
                return self.production_id.with_context(workorder_id_to_finish=self.id)._action_generate_backorder_wizard(self.production_id)
            elif self.production_id.picking_type_id.create_backorder == 'always':
                backorder = self.production_id._split_productions({self.production_id: [self.qty_producing, self.qty_remaining - self.qty_producing]})[1:]
                for workorder in backorder.workorder_ids:
                    if not self.env.context.get('no_start_next', False):
                        workorder.qty_producing = workorder.qty_remaining
                self.production_id.product_qty = self.qty_producing

        else:
            if self.operation_id:
                backorder = (self.production_id.production_group_id.production_ids - self.production_id).filtered(
                    lambda p: p.workorder_ids.filtered(lambda wo: wo.operation_id == self.operation_id).state not in ('cancel', 'done')
                )[:1]
            else:
                index = list(self.production_id.workorder_ids).index(self)
                backorder = (self.production_id.production_group_id.production_ids - self.production_id).filtered(
                    lambda p: index < len(p.workorder_ids) and p.workorder_ids[index].state not in ('cancel', 'done')
                )[:1]

        return self.post_record_production(backorder)

    def post_record_production(self, backorders=False):
        self.button_finish()
        return True

    def do_finish(self):
        self.end_all()
        if self.state != 'done':
            loss_id = self.env['mrp.workcenter.productivity.loss'].search([('loss_type', '=', 'productive')], limit=1)
            if len(loss_id) < 1:
                raise UserError(_("You need to define at least one productivity loss in the category 'Productive'. Create one from the Manufacturing app, menu: Configuration / Productivity Losses."))
            action = self.record_production()
            # In community, time tracking is handled dynamically, but we'll ensure we close if needed
            if action is not True:
                return action
        return True

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
                'default_production_id': self.production_id.id,
                'default_workorder_id': self.id,
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
