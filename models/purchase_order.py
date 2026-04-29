# -*- coding: utf-8 -*-
from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    mrp_production_id = fields.Many2one('mrp.production', string='Manufacturing Order', readonly=True, copy=False)

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    mrp_workorder_id = fields.Many2one('mrp.workorder', string='Work Order', readonly=True, copy=False)

    def write(self, vals):
        res = super(PurchaseOrderLine, self).write(vals)
        if 'qty_received' in vals:
            for line in self:
                if line.qty_received >= line.product_qty and line.mrp_workorder_id and line.mrp_workorder_id.state not in ['done', 'cancel']:
                    if line.mrp_workorder_id.state == 'ready':
                        line.mrp_workorder_id.button_start()
                    line.mrp_workorder_id.button_finish()
        return res
