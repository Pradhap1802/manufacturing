# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    secondary_qty = fields.Float(string='Secondary Qty', digits='Product Unit of Measure')
    secondary_uom_id = fields.Many2one('uom.uom', string='Secondary UoM', related='product_id.secondary_uom_id', readonly=True)

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
