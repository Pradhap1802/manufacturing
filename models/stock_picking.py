# -*- coding: utf-8 -*-
from odoo import models, fields

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    subcontract_workorder_delivery_ids = fields.One2many('mrp.workorder', 'delivery_picking_id', string='Subcontract Delivery Work Orders')
    subcontract_workorder_receipt_ids = fields.One2many('mrp.workorder', 'receipt_picking_id', string='Subcontract Receipt Work Orders')

    def _action_done(self):
        res = super(StockPicking, self)._action_done()
        for picking in self:
            # If this is a receipt from a subcontractor, complete the operation
            for wo in picking.subcontract_workorder_receipt_ids:
                if wo.state not in ['done', 'cancel']:
                    if wo.state == 'ready':
                        wo.button_start()
                    wo.button_finish()
        return res
