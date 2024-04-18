# -*- coding: utf-8 -*-

{
    "name": "Custom Master Data for Millform",
    "version": "17.0.1.0.0",
    "depends": [
        "product",
        "contacts",
        "stock",
        "sale",
    ],
    "category": "Product",
    "author": "Ioppolo & Associates",
    "website": "http://www.ioppolo.com.au/",
    "summary": "Custom Master Data for Millform",
    "description": """
Custom Master Data for Millform
""",
    'data': [
        'security/ir.model.access.csv',
        'data/partner.access.restrictions.csv',
        'data/partner.product.notes.csv',
        'data/partner.lifting.device.csv',
        'views/product_views.xml',
        'views/res_partner_views.xml',
        'views/tekla_views.xml',
        'views/freight_charges_views.xml',
        'views/sale_views.xml',
    ],
    "installable": True,
    'license': 'LGPL-3',
}
