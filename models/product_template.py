# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    secondary_uom_id = fields.Many2one(
        'uom.uom', string='Secondary UoM',
        help="Secondary unit of measure for this product (e.g., KG)."
    )
    secondary_uom_ratio = fields.Float(
        string='Secondary Ratio', default=1.0,
        help="Ratio between Primary UoM and Secondary UoM (e.g., 5 kg/sq.ft)."
    )
    secondary_qty = fields.Float(
        string='Secondary Qty On Hand', compute='_compute_secondary_qty',
        help="Total Quantity on hand in Secondary UoM."
    )

    @api.depends('qty_available', 'secondary_uom_ratio')
    def _compute_secondary_qty(self):
        for product in self:
            product.secondary_qty = product.qty_available * product.secondary_uom_ratio

