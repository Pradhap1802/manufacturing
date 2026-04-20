# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def action_open_shop_floor(self):
        self.ensure_one()
        action = self.env.ref('manufacturing.action_mrp_shop_floor').read()[0]
        action['domain'] = [('production_id', '=', self.id), ('state', 'in', ('ready', 'progress'))]
        action['context'] = {'default_production_id': self.id}
        action['display_name'] = _("Shop Floor - %s") % self.name
        return action
