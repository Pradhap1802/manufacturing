{
    'name': 'Smart Manufacturing',
    'version': '1.0',
    'summary': 'Custom manufacturing features for Odoo 19',
    'category': 'Manufacturing',
    'author': 'ProcessDrive',
    'depends': ['mrp', 'stock', 'hr', 'maintenance'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/mrp_create_bom_wizard_views.xml',
        'views/mrp_workcenter_views.xml',
        'views/mrp_shop_floor_views.xml',
        'views/mrp_quality_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
