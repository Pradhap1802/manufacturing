# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.webmanifest import WebManifest as WebWebManifest
from urllib.parse import quote

class ManufacturingWebManifest(WebWebManifest):

    def _get_scoped_app_icons(self, app_id):
        if app_id == "manufacturing_shop_floor":
            return [{
                'src': '/manufacturing/static/description/icon.png',
                'sizes': 'any',
                'type': 'image/png'
            }]
        return super()._get_scoped_app_icons(app_id)

    def _get_scoped_app_name(self, app_id):
        if app_id == "manufacturing_shop_floor":
            return "Shop Floor"
        return super()._get_scoped_app_name(app_id)

class ShopFloorController(http.Controller):

    @http.route('/shop-floor', type='http', auth='user')
    def shop_floor_redirect(self, **kwargs):
        """Redirect to the shop floor installation page."""
        # Use a clean path for the manifest to avoid scope/origin issues
        path = "shop-floor/app"
        url = f"/scoped_app?app_id=manufacturing_shop_floor&path={path}&app_name=Shop%20Floor"
        return request.redirect(url)

    @http.route('/shop-floor/app', type='http', auth='user')
    def shop_floor_app(self, **kwargs):
        """Dedicated start_url for the PWA that identifies the device and redirects."""
        # Set a persistent cookie to identify this browser as a Shop Floor terminal.
        # This will be picked up by our IrHttp.session_info override to set the home action.
        response = request.redirect("/odoo")
        response.set_cookie('is_shop_floor', '1', max_age=30*24*60*60) # 30 days
        return response
