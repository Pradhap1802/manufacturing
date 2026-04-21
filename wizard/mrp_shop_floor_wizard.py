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

    # Quantity fields decoupled from relation for instant reactive UI updates
    qty_producing = fields.Float('Qty Producing')
    qty_production = fields.Float('Total Qty', readonly=True)
    qty_remaining = fields.Float('Remaining Qty', readonly=True)

    # Duration / timer
    duration = fields.Float('Time Elapsed (min)', related='workorder_id.duration')

    # Scrap
    scrap_qty = fields.Float('Scrap Quantity', default=0.0)
    scrap_reason = fields.Char('Scrap Reason')

    @api.model
    def default_get(self, fields_list):
        res = super(MrpShopFloorWizard, self).default_get(fields_list)
        if 'workorder_id' in res:
            wo = self.env['mrp.workorder'].browse(res['workorder_id'])
            res['qty_producing'] = wo.qty_producing
            res['qty_production'] = wo.qty_production
            res['qty_remaining'] = wo.qty_remaining
        return res

    @api.onchange('qty_producing')
    def _onchange_qty_producing(self):
        for w in self:
            w.qty_remaining = w.qty_production - w.qty_producing

    def action_start(self):
        self.ensure_one()
        self.workorder_id.write({
            'employee_id': self.employee_id.id,
            'qty_producing': self.qty_producing
        })
        return self.workorder_id.button_start()

    def action_pause(self):
        self.ensure_one()
        self.workorder_id.write({'qty_producing': self.qty_producing})
        return self.workorder_id.button_pending()

    def action_finish(self):
        self.ensure_one()
        self.workorder_id.write({'qty_producing': self.qty_producing})
        if self.scrap_qty > 0:
            self.env['stock.scrap'].create({
                'product_id': self.product_id.id,
                'scrap_qty': self.scrap_qty,
                'production_id': self.production_id.id,
                'workorder_id': self.workorder_id.id,
                'location_id': self.production_id.location_src_id.id,
                'scrap_reason': self.scrap_reason,
            })
            
        # Finish the current Work Order
        res = self.workorder_id.button_finish()
        
        # Check if the Manufacturing Order is fully completed (all WO's done or canceled)
        mo = self.production_id
        if all(wo.state in ('done', 'cancel') for wo in mo.workorder_ids):
            # Attempt to mark the MO as done. 
            # If a backorder is needed, Odoo returns the backorder wizard action directly.
            mo_res = mo.button_mark_done()
            if isinstance(mo_res, dict):
                return mo_res  # This pops up the backorder wizard!

        return {'type': 'ir.actions.client', 'tag': 'reload'}

