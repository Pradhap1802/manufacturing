# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class MrpSubcontractingReceiveWizard(models.TransientModel):
    _name = 'mrp.subcontracting.receive.wizard'
    _description = 'Receive Subcontracted Goods'

    workorder_id = fields.Many2one('mrp.workorder', required=True)
    qty_received = fields.Float('Qty Received', required=True)
    product_id = fields.Many2one('product.product', string='Product', related='workorder_id.production_id.product_id', readonly=True)
    finished_qty = fields.Float('Finished Product Qty', related='workorder_id.production_id.product_qty', readonly=True)
    mo_end_date = fields.Date('MO End Date', compute='_compute_dates', readonly=False)
    delivery_date = fields.Date('Delivery Date', compute='_compute_dates', readonly=False)

    @api.depends('workorder_id.production_id.date_finished', 'workorder_id.delivery_picking_id.date_done', 'workorder_id.subcontract_receipt_date')
    def _compute_dates(self):
        for wizard in self:
            wizard.mo_end_date = wizard.workorder_id.production_id.date_finished.date() if wizard.workorder_id.production_id.date_finished else False
            # Use the saved date from the delivery wizard if available
            wizard.delivery_date = wizard.workorder_id.subcontract_receipt_date or (wizard.workorder_id.delivery_picking_id.date_done.date() if wizard.workorder_id.delivery_picking_id.date_done else False)
    rejected_qty = fields.Float('Rejected Qty', default=0.0)
    cost = fields.Monetary('Cost', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='workorder_id.company_currency_id')

    def action_receive(self):
        wo = self.workorder_id
        wo.rejected_qty = self.rejected_qty
        wo.operation_cost = self.cost
        
        # Create and validate receipt picking
        warehouse = wo.production_id.picking_type_id.warehouse_id
        receipt_type = warehouse.in_type_id
        vendor_location = wo.vendor_id.property_stock_supplier
        
        picking = self.env['stock.picking'].create({
            'partner_id': wo.vendor_id.id,
            'picking_type_id': receipt_type.id,
            'location_id': vendor_location.id,
            'location_dest_id': wo.production_id.location_dest_id.id,
            'origin': f"{wo.production_id.name} - {wo.name} (Return)",
            'company_id': wo.company_id.id,
        })
        move = self.env['stock.move'].create({
            'product_id': wo.production_id.product_id.id,
            'product_uom_qty': self.qty_received,
            'product_uom': wo.production_id.product_uom_id.id,
            'picking_id': picking.id,
            'location_id': vendor_location.id,
            'location_dest_id': wo.production_id.location_dest_id.id,
        })
        picking.action_confirm()
        move.quantity = self.qty_received
        picking.button_validate()
        
        wo.receipt_picking_id = picking.id
        
        # We start and finish the workorder to mark the operation as completed
        if wo.state == 'ready':
            wo.button_start()
        if wo.state == 'progress':
            wo.button_finish()
        
        wo.tracking_status = 'received'
