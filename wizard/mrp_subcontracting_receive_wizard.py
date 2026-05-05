# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

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
        production = wo.production_id

        if wo.receipt_picking_id:
            raise UserError(_(
                "A receipt transfer (ref: %s) already exists for this operation."
            ) % wo.receipt_picking_id.name)

        wo.rejected_qty = self.rejected_qty
        wo.operation_cost = self.cost

        # Build receipt: vendor supplier location → production source location
        warehouse = production.picking_type_id.warehouse_id
        receipt_type = warehouse.in_type_id
        vendor_location = wo.vendor_id.property_stock_supplier
        dest_location = production.location_src_id  # back to the production floor

        # Gather components from the outgoing delivery picking
        delivery_moves = wo.delivery_picking_id.move_ids.filtered(
            lambda m: m.state == 'done'
        )
        if not delivery_moves:
            raise UserError(_(
                "No validated delivery moves found on the send-to-vendor transfer. "
                "Please validate the delivery picking from Inventory > Transfers first."
            ))

        # Create the inbound receipt picking (vendor → production floor)
        picking = self.env['stock.picking'].create({
            'partner_id': wo.vendor_id.id,
            'picking_type_id': receipt_type.id,
            'location_id': vendor_location.id,
            'location_dest_id': dest_location.id,
            'origin': f"{production.name} - {wo.name} (Subcontract Return)",
            'company_id': wo.company_id.id,
            'note': _('Processed components returned by subcontractor for operation: %s') % wo.name,
        })

        # Mirror each component from the delivery
        for dmove in delivery_moves:
            self.env['stock.move'].create({
                'description_picking': dmove.product_id.display_name,
                'product_id': dmove.product_id.id,
                'product_uom_qty': dmove.quantity,
                'product_uom': dmove.product_uom.id,
                'picking_id': picking.id,
                'location_id': vendor_location.id,
                'location_dest_id': dest_location.id,
                'origin': picking.origin,
                'company_id': wo.company_id.id,
            })

        picking.action_confirm()
        wo.receipt_picking_id = picking.id
        wo.tracking_status = 'received'

        # Open the receipt picking for the user to review quantities and validate
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': picking.id,
            'target': 'current',
            'name': _('Receive from Subcontractor'),
        }
