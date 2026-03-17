# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class QualityCheckCustom(models.Model):
    _name = 'quality.check.custom'
    _description = 'Quality Check'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char('Reference', readonly=True, default=lambda self: _('New'))
    product_id = fields.Many2one('product.product', string='Product', required=True, tracking=True)
    picking_id = fields.Many2one('stock.picking', string='Picking', tracking=True)
    production_id = fields.Many2one('mrp.production', string='Production', tracking=True)
    workorder_id = fields.Many2one('mrp.workorder', string='Work Order', tracking=True)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user, tracking=True)
    team_id = fields.Many2one('quality.team.custom', string='Team', tracking=True)
    state = fields.Selection([
        ('none', 'To Do'),
        ('pass', 'Passed'),
        ('fail', 'Failed')], string='Status', default='none', tracking=True)
    control_date = fields.Datetime('Control Date', default=fields.Datetime.now, tracking=True)
    note = fields.Text('Internal Notes')

    def action_pass(self):
        self.write({'state': 'pass', 'control_date': fields.Datetime.now()})

    def action_fail(self):
        self.write({'state': 'fail', 'control_date': fields.Datetime.now()})

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('quality.check.custom') or _('New')
        return super().create(vals_list)

class QualityAlertCustom(models.Model):
    _name = 'quality.alert.custom'
    _description = 'Quality Alert'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char('Reference', readonly=True, default=lambda self: _('New'))
    product_id = fields.Many2one('product.product', string='Product', tracking=True)
    production_id = fields.Many2one('mrp.production', string='Production', tracking=True)
    workorder_id = fields.Many2one('mrp.workorder', string='Work Order', tracking=True)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user, tracking=True)
    description = fields.Text('Description')
    cause = fields.Text('Root Cause')
    action_corrective = fields.Text('Corrective Action')
    action_preventive = fields.Text('Preventive Action')
    state = fields.Selection([
        ('new', 'New'),
        ('confirmed', 'Confirmed'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed')], default='new', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('quality.alert.custom') or _('New')
        return super().create(vals_list)

class QualityTeamCustom(models.Model):
    _name = 'quality.team.custom'
    _description = 'Quality Team'
    _inherit = ['mail.thread']

    name = fields.Char('Team Name', required=True)
    user_id = fields.Many2one('res.users', string='Team Leader')
    email_alias = fields.Char('Email Alias')
