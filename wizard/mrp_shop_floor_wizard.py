# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class MrpShopFloorWizard(models.TransientModel):
    _name = 'mrp.shop.floor.wizard'
    _description = 'Shop Floor Interaction Wizard'

    workorder_id = fields.Many2one('mrp.workorder', string='Work Order', required=True)
    production_id = fields.Many2one('mrp.production', related='workorder_id.production_id')
    product_id = fields.Many2one('product.product', related='workorder_id.product_id')

    employee_id = fields.Many2one('hr.employee', string='Employee')

    state = fields.Selection(related='workorder_id.state')
    
    wizard_mode = fields.Selection([
        ('pause', 'Pause'),
        ('resume', 'Resume'),
        ('finish', 'Finish'),
        ('manage', 'Manage')
    ], string="Mode", default='manage')

    # Finished Product Quantity fields
    qty_producing = fields.Float('Qty Currently Producing')
    qty_production = fields.Float('Total Qty', readonly=True)
    qty_remaining = fields.Float('Remaining Qty', readonly=True)

    # Duration / timer
    duration = fields.Float('Time Elapsed (min)', related='workorder_id.duration')

    # Scrap Logic (Dropdown based - RAW MATERIALS ONLY)
    scrap_product_id = fields.Many2one('product.product', string='Raw Material to Scrap')
    scrap_qty = fields.Float('Scrap Quantity', default=0.0)
    scrap_reason = fields.Char('Scrap Reason')
    
    # Helper for dropdown domain restriction
    scrap_allowed_product_ids = fields.Many2many('product.product', string='Allowed Scrap Products')

    # Downtime Tracking (captured when pausing)
    downtime_reason = fields.Selection([
        ('breakdown',   'Machine Breakdown'),
        ('material',    'Material Shortage'),
        ('quality',     'Quality Hold'),
        ('maintenance', 'Planned Maintenance'),
        ('operator',    'Operator Absent'),
        ('changeover',  'Product Changeover'),
        ('other',       'Other'),
    ], string='Pause Reason')
    downtime_notes = fields.Text('Notes', placeholder='Describe the issue briefly...')

    # Component Visibility (Keep as readonly list for operator reference)
    component_line_ids = fields.One2many('mrp.shop.floor.wizard.line', 'wizard_id', string='Materials List')

    @api.model
    def default_get(self, fields_list):
        res = super(MrpShopFloorWizard, self).default_get(fields_list)
        if 'workorder_id' in res:
            wo = self.env['mrp.workorder'].browse(res['workorder_id'])
            res['qty_producing'] = wo.qty_producing
            res['qty_production'] = wo.qty_production
            res['qty_remaining'] = wo.qty_remaining
            
            # 1. Populate Materials List (Read-only)
            lines = []
            allowed_ids = [] # EXCLUDE finished product (wo.product_id.id)
            for move in wo.production_id.move_raw_ids:
                allowed_ids.append(move.product_id.id)
                lines.append((0, 0, {
                    'product_id': move.product_id.id,
                    'qty_planned': move.product_uom_qty,
                    'qty_done': move.quantity,
                    'product_uom_id': move.product_uom.id,
                }))
            res['component_line_ids'] = lines
            
            # 2. Set domain for EXACT raw materials only
            res['scrap_allowed_product_ids'] = [(6, 0, allowed_ids)]
            
        return res

    @api.onchange('qty_producing')
    def _onchange_qty_producing(self):
        for w in self:
            w.qty_remaining = w.qty_production - w.qty_producing

    def _handle_scrap(self):
        """Handle scrap for the selected raw material component and auto-validate."""
        if self.scrap_qty > 0 and self.scrap_product_id:
            # Only scrap if a specific component is selected
            scrap = self.env['stock.scrap'].create({
                'product_id': self.scrap_product_id.id,
                'scrap_qty': self.scrap_qty,
                'production_id': self.production_id.id,
                'workorder_id': self.workorder_id.id,
                'location_id': self.production_id.location_src_id.id,
                'scrap_reason': self.scrap_reason or _('Raw Material Scrap (Shop Floor)'),
            })
            # Automatically confirm/validate the scrap record
            scrap.action_validate()

            # Clear fields
            self.scrap_qty = 0.0
            self.scrap_reason = False
            self.scrap_product_id = False

    def action_start(self):
        self.ensure_one()
        self._handle_scrap()
        self.workorder_id.write({
            'employee_id': self.employee_id.id,
            'qty_producing': self.qty_producing
        })
        return self.workorder_id.button_start()

    def action_pause(self):
        self.ensure_one()
        self._handle_scrap()
        self.workorder_id.write({'qty_producing': self.qty_producing})
        res = self.workorder_id.button_pending()
        # Write downtime reason to the most recent productivity (time log) record
        if self.downtime_reason:
            last_timer = self.env['mrp.workcenter.productivity'].search([
                ('workorder_id', '=', self.workorder_id.id),
                ('date_end', '!=', False)
            ], order='date_end desc', limit=1)
            if last_timer:
                last_timer.write({
                    'downtime_reason': self.downtime_reason,
                    'downtime_notes': self.downtime_notes,
                })
        return res

    def action_finish(self):
        self.ensure_one()
        self._handle_scrap()
        self.workorder_id.write({'qty_producing': self.qty_producing})
        res = self.workorder_id.button_finish()
        mo = self.production_id
        if all(wo.state in ('done', 'cancel') for wo in mo.workorder_ids):
            mo_res = mo.button_mark_done()
            if isinstance(mo_res, dict):
                return mo_res
        return {'type': 'ir.actions.client', 'tag': 'reload'}

class MrpShopFloorWizardLine(models.TransientModel):
    _name = 'mrp.shop.floor.wizard.line'
    _description = 'Shop Floor Wizard Material View'

    wizard_id = fields.Many2one('mrp.shop.floor.wizard', string='Wizard')
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    qty_planned = fields.Float('Planned Qty', readonly=True)
    qty_done = fields.Float('Consumed Qty', readonly=True)
    product_uom_id = fields.Many2one('uom.uom', string='UoM', readonly=True)
