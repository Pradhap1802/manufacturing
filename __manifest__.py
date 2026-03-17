# -*- coding: utf-8 -*-
{
    'name': 'Smart Manufacturing Ecosystem',
    'version': '1.0',
    'category': 'Manufacturing',
    'summary': 'Enhanced Manufacturing with Quality Control, IoT, and Smart Monitoring',
    'description': """
        Custom Manufacturing addon for Odoo Community.
        Features:
        - Custom Quality Checks & Alerts
        - Smart Control Center Monitoring
        - Machine & IoT Management
        - Full Chatter & Activity integration
    """,
    'author': 'ProcessDrive',
    'depends': ['mrp', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/quality_custom_views.xml',
        'views/mrp_extensions_views.xml',
        'views/mrp_bom_extensions_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
