# -*- coding: utf-8 -*-

{
    "name": "Reports Customization",
    "version": "17.0",
    "depends": [
        "base", "sale", "purchase", "stock", "account", "contacts", "sale_management", "sale_pdf_quote_builder",
    ],
    "category": "Sale",
    "author": "Ioppolo & Associates",
    "website": "http://www.ioppolo.com.au/",
    "summary": "Reports Customization for Millform",
    "description": """
Reports Customization for Millform
""",
    'data': [
        'data/report_paper_format.xml',
        'reports/ir_actions_report.xml',
        'reports/sale_order_template.xml',
        'reports/quotation_template.xml',
        'reports/purchase_order_report.xml',
        'reports/delivery_slip_report.xml',
    ],
    "installable": True,
    'license': 'LGPL-3',
}
