# -*- coding: utf-8 -*-
from odoo import models, fields, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    subcontract_workorder_delivery_ids = fields.One2many('mrp.workorder', 'delivery_picking_id', string='Subcontract Delivery Work Orders')
    subcontract_workorder_receipt_ids = fields.One2many('mrp.workorder', 'receipt_picking_id', string='Subcontract Receipt Work Orders')

    def _action_done(self):
        res = super(StockPicking, self)._action_done()
        for picking in self:
            # When a subcontractor receipt is validated, auto-finish the linked work order
            for wo in picking.subcontract_workorder_receipt_ids:
                if wo.state in ('done', 'cancel'):
                    continue
                try:
                    # Ensure the work order is in 'progress' before finishing
                    if wo.state == 'pending':
                        wo.write({'state': 'ready'})
                    if wo.state == 'ready':
                        # Use sudo to bypass employee validation for automated completion
                        wo.sudo().button_start()
                    if wo.state == 'progress':
                        wo.sudo().button_finish()
                    # Safety net: force tracking_status to 'done' if still not done
                    if wo.tracking_status not in ('done', 'cancel'):
                        wo.write({'tracking_status': 'done'})
                except Exception:
                    # If auto-finish fails, force the tracking status update
                    wo.write({'tracking_status': 'done'})
        return res
