# -*- coding: utf-8 -*-
from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_manufacturing_multi_uom = fields.Boolean(
        string="Manage Multi UOM",
        group='base.group_user',
        implied_group='manufacturing.group_manufacturing_multi_uom',
        help="Enables the ability to manage products in two different units of measure simultaneously."
    )
