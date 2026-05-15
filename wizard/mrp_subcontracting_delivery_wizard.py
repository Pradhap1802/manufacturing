# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MrpSubcontractingDeliveryWizard(models.TransientModel):
    _name = 'mrp.subcontracting.delivery.wizard'
    _description = 'Send Components to Subcontractor'

    workorder_id = fields.Many2one('mrp.workorder', required=True)
    production_id = fields.Many2one('mrp.production', related='workorder_id.production_id', readonly=True)
    vendor_id = fields.Many2one('res.partner', related='workorder_id.vendor_id', readonly=True)
    
    line_ids = fields.One2many('mrp.subcontracting.delivery.wizard.line', 'wizard_id', string='Components to Send')
    product_id = fields.Many2one('product.product', string='Finished Product', related='workorder_id.production_id.product_id', readonly=True)
    mo_start_date = fields.Date('MO Start Date', compute='_compute_dates', readonly=True)
    receipt_date = fields.Date('Receipt Date', compute='_compute_dates', readonly=False)
    delivery_date = fields.Date('Delivery Date', compute='_compute_dates', readonly=True)

    @api.depends('workorder_id.production_id.date_start', 'workorder_id.production_id.date_finished', 'workorder_id.delivery_picking_id.date_done')
    def _compute_dates(self):
        for wizard in self:
            wizard.mo_start_date = wizard.workorder_id.production_id.date_start.date() if wizard.workorder_id.production_id.date_start else False
            wizard.receipt_date = wizard.workorder_id.production_id.date_finished.date() if wizard.workorder_id.production_id.date_finished else False
            wizard.delivery_date = wizard.workorder_id.delivery_picking_id.date_done.date() if wizard.workorder_id.delivery_picking_id.date_done else False

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'line_ids' in fields_list and res.get('workorder_id'):
            wo = self.env['mrp.workorder'].browse(res['workorder_id'])
            lines = []
            for move in wo.production_id.move_raw_ids:
                lines.append((0, 0, {
                    'product_id': move.product_id.id,
                    'demand_qty': move.product_uom_qty,
                    'qty_to_send': move.product_uom_qty,
                    'uom_id': move.product_uom.id,
                    'move_id': move.id,
                }))
            res['line_ids'] = lines
        return res

    def action_send(self):
        self.ensure_one()
        wo = self.workorder_id
        
        warehouse = wo.production_id.picking_type_id.warehouse_id
        delivery_type = warehouse.out_type_id
        vendor_location = wo.vendor_id.property_stock_supplier

        if not delivery_type or not vendor_location:
            raise UserError(_("Warehouse delivery type or Vendor location is not configured properly."))

        picking = self.env['stock.picking'].create({
            'partner_id': wo.vendor_id.id,
            'picking_type_id': delivery_type.id,
            'location_id': wo.production_id.location_src_id.id,
            'location_dest_id': vendor_location.id,
            'origin': f"{wo.production_id.name} - {wo.name} (Send)",
            'company_id': wo.company_id.id,
        })
        
        for line in self.line_ids:
            if line.qty_to_send <= 0:
                continue
            self.env['stock.move'].create({
                'description_picking': line.product_id.display_name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.qty_to_send,
                'product_uom': line.uom_id.id,
                'picking_id': picking.id,
                'location_id': wo.production_id.location_src_id.id,
                'location_dest_id': vendor_location.id,
            })
            
        picking.action_confirm()
        picking.action_assign()
        
        wo.delivery_picking_id = picking.id
        return {'type': 'ir.actions.act_window_close'}

class MrpSubcontractingDeliveryWizardLine(models.TransientModel):
    _name = 'mrp.subcontracting.delivery.wizard.line'
    _description = 'Subcontracting Delivery Line'

    wizard_id = fields.Many2one('mrp.subcontracting.delivery.wizard')
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    demand_qty = fields.Float('Demand', readonly=True)
    qty_to_send = fields.Float('Actual Send')
    uom_id = fields.Many2one('uom.uom', string='UoM', readonly=True)
    move_id = fields.Many2one('stock.move', string='Source Move')
