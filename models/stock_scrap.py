# -*- coding: utf-8 -*-
from odoo import models, fields

class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    scrap_reason = fields.Char('Scrap Reason')
