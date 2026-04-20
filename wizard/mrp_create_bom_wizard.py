# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MrpCreateBomWizard(models.TransientModel):
    _name = 'mrp.create.bom.wizard'
    _description = 'Create BOM from selected products'

    product_tmpl_id = fields.Many2one('product.template', string='Finished Product', required=True)
    product_qty = fields.Float(string='Finished Product Quantity', default=1.0, required=True)
    line_ids = fields.One2many('mrp.create.bom.wizard.line', 'wizard_id', string='Components')
    operation_ids = fields.One2many('mrp.create.bom.wizard.operation', 'wizard_id', string='Operations')


    @api.model
    def default_get(self, fields_list):
        res = super(MrpCreateBomWizard, self).default_get(fields_list)
        if self.env.context.get('active_model') == 'product.template' and self.env.context.get('active_ids'):
            product_tmpl_ids = self.env.context.get('active_ids')
            line_vals = []
            for tmpl_id in product_tmpl_ids:
                line_vals.append((0, 0, {
                    'product_tmpl_id': tmpl_id,
                    'product_qty': 1.0,
                }))
            res['line_ids'] = line_vals
        return res

    def action_create_bom(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("No components selected."))

        # Create the BoM
        bom_vals = {
            'product_tmpl_id': self.product_tmpl_id.id,
            'product_qty': self.product_qty,
            'type': 'normal',
            'bom_line_ids': [],
            'operation_ids': []
        }

        # Add Components
        for line in self.line_ids:
            product_product = line.product_tmpl_id.product_variant_id or line.product_tmpl_id.product_variant_ids[:1]
            if not product_product:
                continue
            
            bom_vals['bom_line_ids'].append((0, 0, {
                'product_id': product_product.id,
                'product_qty': line.product_qty,
            }))

        # Add Operations
        for op in self.operation_ids:
            bom_vals['operation_ids'].append((0, 0, {
                'name': op.name,
                'workcenter_id': op.workcenter_id.id,
                'time_cycle_manual': op.time_cycle_manual,
            }))

        bom = self.env['mrp.bom'].create(bom_vals)

        return {
            'name': _('Bill of Material'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.bom',
            'res_id': bom.id,
            'view_mode': 'form',
            'target': 'current',
        }

class MrpCreateBomWizardLine(models.TransientModel):
    _name = 'mrp.create.bom.wizard.line'
    _description = 'Wizard Component Line'

    wizard_id = fields.Many2one('mrp.create.bom.wizard', string='Wizard')
    product_tmpl_id = fields.Many2one('product.template', string='Component', required=True)
    product_qty = fields.Float(string='Quantity', default=1.0, required=True)

class MrpCreateBomWizardOperation(models.TransientModel):
    _name = 'mrp.create.bom.wizard.operation'
    _description = 'Wizard Operation'

    wizard_id = fields.Many2one('mrp.create.bom.wizard', string='Wizard')
    name = fields.Char('Operation', required=True)
    workcenter_id = fields.Many2one('mrp.workcenter', 'Work Center', required=True)
    time_cycle_manual = fields.Float('Duration (minutes)', default=60.0)
