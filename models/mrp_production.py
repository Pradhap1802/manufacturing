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

    subcontract_picking_count = fields.Integer(compute='_compute_subcontract_picking_count')

    def _compute_subcontract_picking_count(self):
        for production in self:
            pickings = production.workorder_ids.mapped('delivery_picking_id') | production.workorder_ids.mapped('receipt_picking_id')
            production.subcontract_picking_count = len(pickings)

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

    def action_view_custom_cost_analysis(self):
        self.ensure_one()
        return {
            'name': _('Cost Analysis'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'form',
            'res_id': self.id,
            'view_id': self.env.ref('manufacturing.mrp_production_cost_analysis_form_view').id,
            'target': 'new',
        }

    def action_view_subcontract_pickings(self):
        self.ensure_one()
        pickings = self.workorder_ids.mapped('delivery_picking_id') | self.workorder_ids.mapped('receipt_picking_id')
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        action['domain'] = [('id', 'in', pickings.ids)]
        action['context'] = {'create': False}
        return action
