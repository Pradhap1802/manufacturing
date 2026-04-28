# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, date

class MrpWorkcenterProductivity(models.Model):
    _inherit = 'mrp.workcenter.productivity'

    employee_id = fields.Many2one('hr.employee', string='Operator')
    total_cost = fields.Float('Total Cost', compute='_compute_total_cost', store=True)

    # Downtime tracking
    downtime_reason = fields.Selection([
        ('breakdown',   'Machine Breakdown'),
        ('material',    'Material Shortage'),
        ('quality',     'Quality Hold'),
        ('maintenance', 'Planned Maintenance'),
        ('operator',    'Operator Absent'),
        ('changeover',  'Product Changeover'),
        ('other',       'Other'),
    ], string='Downtime Reason')
    downtime_notes = fields.Text('Downtime Notes')

    def _compute_total_cost(self):
        for time in self:
            duration = time.duration / 60.0  # Duration is in minutes
            employee = time.employee_id.sudo()
            rate = employee.hourly_cost if employee else time.workcenter_id.costs_hour
            time.total_cost = duration * rate


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    # Production target tracking
    daily_target_qty = fields.Float(
        string='Daily Target Qty',
        help="Expected number of units to produce per day at this work center."
    )

    qty_produced_today = fields.Float(
        string='Produced Today',
        compute='_compute_today_production',
        help="Total quantity of finished work orders completed today."
    )

    target_achievement_pct = fields.Float(
        string='Target Achievement (%)',
        compute='_compute_today_production',
        help="Percentage of daily target achieved today."
    )

    @api.depends('daily_target_qty')
    def _compute_today_production(self):
        today_start = datetime.combine(date.today(), datetime.min.time())
        for wc in self:
            done_orders = self.env['mrp.workorder'].search([
                ('workcenter_id', '=', wc.id),
                ('state', '=', 'done'),
                ('date_finished', '>=', fields.Datetime.to_string(today_start)),
            ])
            qty = sum(done_orders.mapped('qty_producing'))
            wc.qty_produced_today = qty
            if wc.daily_target_qty:
                wc.target_achievement_pct = (qty / wc.daily_target_qty) * 100.0
            else:
                wc.target_achievement_pct = 0.0
