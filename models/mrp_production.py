# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    secondary_qty = fields.Float(string='Secondary Qty', digits='Product Unit of Measure')
    secondary_uom_id = fields.Many2one('uom.uom', string='Secondary UoM', related='product_id.secondary_uom_id', readonly=True)

    quality_alert_count = fields.Integer(compute='_compute_quality_alert_count')
    maintenance_count = fields.Integer(compute='_compute_maintenance_count')

    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency")
    employee_cost_total = fields.Monetary(
        string='Total Labour Cost',
        compute='_compute_employee_cost_total',
        currency_field='company_currency_id',
        help="Total cost of employee labour logged on work orders."
    )
    subcontract_cost_total = fields.Monetary(
        string='Total Subcontract Cost',
        compute='_compute_subcontract_cost_total',
        currency_field='company_currency_id'
    )
    total_operation_cost = fields.Monetary(
        string='Total Operations Cost',
        compute='_compute_total_operation_cost',
        currency_field='company_currency_id'
    )
    mo_progress_percent = fields.Float(string='Progress %', compute='_compute_mo_progress', store=True)

    # Subcontracting Fields
    purchase_order_ids = fields.One2many('purchase.order', 'mrp_production_id', string='Subcontracting POs')
    subcontract_po_count = fields.Integer(compute='_compute_subcontract_po_count')

    def _compute_subcontract_po_count(self):
        for production in self:
            production.subcontract_po_count = len(production.purchase_order_ids)

    @api.depends('workorder_ids.time_ids.total_cost')
    def _compute_employee_cost_total(self):
        for production in self:
            production.employee_cost_total = sum(production.mapped('workorder_ids.time_ids.total_cost'))

    @api.depends('workorder_ids.operation_cost', 'workorder_ids.is_subcontracted')
    def _compute_subcontract_cost_total(self):
        for production in self:
            subcontract_wos = production.workorder_ids.filtered(lambda w: w.is_subcontracted)
            production.subcontract_cost_total = sum(subcontract_wos.mapped('operation_cost'))

    @api.depends('employee_cost_total', 'subcontract_cost_total')
    def _compute_total_operation_cost(self):
        for production in self:
            production.total_operation_cost = production.employee_cost_total + production.subcontract_cost_total

    @api.depends('workorder_ids.state')
    def _compute_mo_progress(self):
        for production in self:
            total_wos = len(production.workorder_ids)
            if total_wos == 0:
                production.mo_progress_percent = 0.0
            else:
                done_wos = len(production.workorder_ids.filtered(lambda wo: wo.state in ['done', 'cancel']))
                production.mo_progress_percent = (done_wos / float(total_wos)) * 100.0

    def _compute_quality_alert_count(self):
        for production in self:
            production.quality_alert_count = self.env['mrp.quality.alert'].search_count([
                ('production_id', '=', production.id)
            ])

    def _compute_maintenance_count(self):
        for production in self:
            production.maintenance_count = self.env['maintenance.request'].search_count([
                ('production_id', '=', production.id)
            ])

    @api.onchange('secondary_qty')
    def _onchange_secondary_qty(self):
        if self.secondary_qty and self.product_id.secondary_uom_ratio:
            self.product_qty = self.secondary_qty / self.product_id.secondary_uom_ratio

    @api.onchange('product_qty')
    def _onchange_product_qty_multi(self):
        if self.product_qty and self.product_id.secondary_uom_ratio:
            self.secondary_qty = self.product_qty * self.product_id.secondary_uom_ratio

    def action_open_shop_floor(self):
        self.ensure_one()
        action = self.env.ref('manufacturing.action_mrp_shop_floor').read()[0]
        action['domain'] = [('production_id', '=', self.id), ('state', 'in', ('ready', 'progress'))]
        action['context'] = {'default_production_id': self.id}
        action['display_name'] = _("Shop Floor - %s") % self.name
        return action

    def action_view_quality_alerts(self):
        self.ensure_one()
        action = self.env.ref('manufacturing.action_mrp_quality_alert_primary').read()[0]
        action['domain'] = [('production_id', '=', self.id)]
        action['context'] = {
            'default_production_id': self.id,
            'default_product_id': self.product_id.id,
        }
        return action

    def action_view_maintenance_requests(self):
        self.ensure_one()
        action = self.env.ref('maintenance.hr_equipment_request_action').read()[0]
        action['domain'] = [('production_id', '=', self.id)]
        action['context'] = {
            'default_production_id': self.id,
        }
        return action

    def button_mark_done(self):
        for production in self:
            unfinished_workorders = production.workorder_ids.filtered(lambda wo: wo.state not in ('done', 'cancel'))
            if unfinished_workorders:
                raise UserError(_("Manufacturing Completion Rule Enforced: You cannot mark the Manufacturing Order as Done until all operations (including subcontracted ones) are completed."))
        return super(MrpProduction, self).button_mark_done()

    def _plan_workorders(self, replan=False):
        res = super(MrpProduction, self)._plan_workorders(replan=replan)
        self._generate_subcontracting_pos()
        return res
        
    def _generate_subcontracting_pos(self):
        """ Automatically generate Purchase Orders and Pickings for subcontracted work orders. """
        PurchaseOrder = self.env['purchase.order']
        PurchaseOrderLine = self.env['purchase.order.line']
        StockPicking = self.env['stock.picking']
        StockMove = self.env['stock.move']

        for production in self:
            warehouse = production.picking_type_id.warehouse_id
            if not warehouse:
                warehouse = self.env['stock.warehouse'].search([('company_id', '=', production.company_id.id)], limit=1)
                
            delivery_type = warehouse.out_type_id
            receipt_type = warehouse.in_type_id
            
            sub_workorders = production.workorder_ids.filtered(lambda wo: wo.is_subcontracted and not wo.purchase_order_id)
            if not sub_workorders:
                continue
                
            # Group by Vendor
            wo_by_vendor = {}
            for wo in sub_workorders:
                if wo.vendor_id:
                    wo_by_vendor.setdefault(wo.vendor_id, []).append(wo)
                    
            for vendor, workorders in wo_by_vendor.items():
                po = PurchaseOrder.create({
                    'partner_id': vendor.id,
                    'mrp_production_id': production.id,
                    'origin': production.name,
                })
                for wo in workorders:
                    if not wo.subcontract_service_id:
                        continue
                    po_line = PurchaseOrderLine.create({
                        'order_id': po.id,
                        'product_id': wo.subcontract_service_id.id,
                        'name': f"Subcontracted Operation: {wo.name} ({production.name})",
                        'product_qty': wo.qty_production,
                        'product_uom': wo.subcontract_service_id.uom_id.id,
                        'price_unit': wo.subcontract_service_id.standard_price,
                        'date_planned': wo.date_planned_start or fields.Datetime.now(),
                    })
                    
                    wo.write({
                        'purchase_order_id': po.id,
                        'purchase_line_id': po_line.id,
                    })
                    
    def action_view_subcontract_pos(self):
        self.ensure_one()
        return {
            'name': _('Subcontracting POs'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': [('mrp_production_id', '=', self.id)],
            'context': {'default_mrp_production_id': self.id},
        }
