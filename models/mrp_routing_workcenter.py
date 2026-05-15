# -*- coding: utf-8 -*-
from odoo import models, fields

class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    is_subcontracted = fields.Boolean(string='Is Subcontracted', default=False, help="Check this if this operation is performed by an external vendor.")
    vendor_id = fields.Many2one('res.partner', string='Subcontractor Vendor', domain="[('supplier_rank', '>', 0)]", help="The vendor who performs this operation.")
