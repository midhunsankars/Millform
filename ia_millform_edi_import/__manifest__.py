# -*- coding: utf-8 -*-

{
    "name": "Millform EDI Import",
    "version": "17.0.1.0.0",
    "depends": [
        "stock",
        "purchase",
        "mrp",
        "purchase_stock",
        "purchase_mrp",
        "ia_master_data",
        "ia_external_dbsource",
    ],
    "category": "Stock",
    "author": "Ioppolo & Associates",
    "website": "http://www.ioppolo.com.au/",
    "summary": "Sales Customization for Millform",
    "description": """
Millform EDI Import
Millform SLIT Form
""",
    'data': [
        'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        'views/edi_import_config_views.xml',
        'views/edi_import_picking.xml',
        'views/edi_import_slitlist.xml',
        'views/edi_product_slit.xml',
        'views/edi_slitting_order.xml',
        'views/edi_slit_coil_order_queue.xml',
        'views/edi_bulk_coil_order_queue.xml',
        'views/edi_bulk_coil_line.xml',
        'views/edi_menu_views.xml',
        'views/common_log_book_edi_views.xml',
        'views/purchase_views.xml',
        'views/stock_quant_views.xml',
    ],
    "installable": True,
    'license': 'LGPL-3',
}
