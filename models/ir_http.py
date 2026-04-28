# -*- coding: utf-8 -*-
from odoo import models
from odoo.http import request

class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        result = super(IrHttp, self).session_info()
        # The Shop Floor login wizard should only open when explicitly accessed via the menu.
        # We removed the home_action_id override here to prevent the wizard from automatically 
        # appearing every time the user updates the addon or loads the Odoo backend.
        return result
