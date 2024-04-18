# -*- coding: utf-8 -*-

{
    "name": "Transport Management System for Millform",
    "version": "17.0.1.0.0",
    "depends": [
        "stock",
        "ia_master_data",
        "ia_sale",
    ],
    "category": "Stock",
    "author": "Ioppolo & Associates",
    "website": "http://www.ioppolo.com.au/",
    "summary": "Transport Management System for Millform",
    "description": """
Transport Management System for Millform
""",
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/tms_views_menus.xml',
        'views/sale_views.xml',
        'views/stock_views.xml',
        'wizard/allocate_loads_views.xml',
        'wizard/bundle_allocate_loads_views.xml'
    ],
    "installable": True,
    'license': 'LGPL-3',
}
