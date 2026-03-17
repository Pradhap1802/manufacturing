# -*- coding: utf-8 -*-
from odoo import models, fields, api

class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    costs_hour_labour = fields.Float(string='Labour Cost per hour', default=0.0, help='Hourly labour cost.')

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    material_cost = fields.Float(string='Material Cost', compute='_compute_bom_costs')
    workcenter_cost = fields.Float(string='Work Center Cost', compute='_compute_bom_costs')
    labour_cost = fields.Float(string='Labour Cost', compute='_compute_bom_costs')

    @api.depends('bom_line_ids', 'bom_line_ids.product_id', 'bom_line_ids.product_qty', 'operation_ids', 'operation_ids.time_total', 'operation_ids.workcenter_id.costs_hour', 'operation_ids.workcenter_id.costs_hour_labour')
    def _compute_bom_costs(self):
        for bom in self:
            material_cost = 0.0
            for line in bom.bom_line_ids:
                # Use standard_price as cost
                material_cost += line.product_id.standard_price * line.product_qty
            
            wc_cost = 0.0
            labour_cost = 0.0
            for op in bom.operation_ids:
                duration_hours = op.time_total / 60.0
                wc_cost += duration_hours * op.workcenter_id.costs_hour
                labour_cost += duration_hours * op.workcenter_id.costs_hour_labour
            
            bom.material_cost = material_cost
            bom.workcenter_cost = wc_cost
            bom.labour_cost = labour_cost
