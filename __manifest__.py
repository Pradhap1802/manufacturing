{
    'name': 'Smart Manufacturing',
    'version': '1.0',
    'summary': 'Custom manufacturing features for Odoo 19',
    'category': 'Manufacturing',
    'author': 'ProcessDrive',
    'depends': ['mrp', 'stock', 'hr', 'maintenance'],
    'data': [
        'security/manufacturing_groups.xml',
        'security/ir.model.access.csv',
        'wizard/mrp_create_bom_wizard_views.xml',
        'wizard/mrp_shop_floor_wizard_views.xml',
        'views/mrp_workcenter_views.xml',
        'views/mrp_shop_floor_views.xml',
        'views/mrp_quality_views.xml',
        'views/mrp_production_views.xml',
        'views/res_config_settings_views.xml',
        'views/product_template_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'manufacturing/static/src/xml/shop_floor_kanban.xml',
            'manufacturing/static/src/js/shop_floor_kanban.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
