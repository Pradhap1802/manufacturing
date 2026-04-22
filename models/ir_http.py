# -*- coding: utf-8 -*-
from odoo import models
from odoo.http import request

class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        result = super(IrHttp, self).session_info()
        # If the user is identified as being in the "Shop Floor" PWA context via cookie
        if request and request.httprequest.cookies.get('is_shop_floor') == '1':
            action = self.env.ref('manufacturing.action_mrp_shop_floor_login', raise_if_not_found=False)
            if action:
                result['home_action_id'] = action.id
        return result
