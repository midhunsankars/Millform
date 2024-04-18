# -*- coding: utf-8 -*-

{
    "name": "Millform Connex API",
    "version": "17.0.1.0.0",
    "depends": [
        "sale",
        "purchase_mrp",
        "ia_sale",
        "ia_mrp_sale",
    ],
    "category": "Sales/Sales",
    "author": "Ioppolo & Associates",
    "website": "http://www.ioppolo.com.au/",
    "summary": "Connex API Connection module for Millform",
    "description": """
Millform Connex API
""",
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings.xml',
        'views/mrp_production.xml',
        'views/product_views.xml',
    ],
    "installable": True,
    'license': 'LGPL-3',
}
