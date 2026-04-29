# -*- coding: utf-8 -*-
from odoo import models, fields, _

class MrpSubcontractingReceiveWizard(models.TransientModel):
    _name = 'mrp.subcontracting.receive.wizard'
    _description = 'Receive Subcontracted Goods'

    workorder_id = fields.Many2one('mrp.workorder', required=True)
    qty_received = fields.Float('Qty Received', required=True)
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
            'name': wo.production_id.product_id.name,
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
