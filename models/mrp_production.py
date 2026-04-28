# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

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

    @api.depends('workorder_ids.time_ids.total_cost')
    def _compute_employee_cost_total(self):
        for production in self:
            production.employee_cost_total = sum(production.mapped('workorder_ids.time_ids.total_cost'))

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
