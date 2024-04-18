# -*- coding: utf-8 -*-

{
    "name": "Sales Customization for Millform",
    "version": "17.0.1.0.0",
    "depends": [
        "sale",
        "sale_stock",
        "field_timepicker",
        "sale_management",
    ],
    "category": "Sale",
    "author": "Ioppolo & Associates",
    "website": "http://www.ioppolo.com.au/",
    "summary": "Sales Customization for Millform",
    "description": """
Sales Customization for Millform
""",
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/res_partner_views.xml',
    ],
    "installable": True,
    'license': 'LGPL-3',
}
