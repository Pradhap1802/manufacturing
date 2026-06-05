# -*- coding: utf-8 -*-
from odoo import models, fields

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    categ_id = fields.Many2one(
        'product.category',
        related='product_tmpl_id.categ_id',
        string='Product Category',
        store=True,
        readonly=True
    )
