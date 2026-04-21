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

    # Quantity fields
    qty_producing = fields.Float('Qty Producing', related='workorder_id.qty_producing', readonly=False)
    qty_production = fields.Float('Total Qty', related='workorder_id.qty_production')
    qty_remaining = fields.Float('Remaining Qty', related='workorder_id.qty_remaining')

    # Duration / timer
    duration = fields.Float('Time Elapsed (min)', related='workorder_id.duration')

    # Scrap
    scrap_qty = fields.Float('Scrap Quantity', default=0.0)
    scrap_reason = fields.Char('Scrap Reason')

    def action_start(self):
        self.ensure_one()
        self.workorder_id.write({'employee_id': self.employee_id.id})
        return self.workorder_id.button_start()

    def action_pause(self):
        self.ensure_one()
        return self.workorder_id.button_pending()

    def action_finish(self):
        self.ensure_one()
        if self.scrap_qty > 0:
            self.env['stock.scrap'].create({
                'product_id': self.product_id.id,
                'scrap_qty': self.scrap_qty,
                'production_id': self.production_id.id,
                'workorder_id': self.workorder_id.id,
                'location_id': self.production_id.location_src_id.id,
                'scrap_reason': self.scrap_reason,
            })
        return self.workorder_id.button_finish()
