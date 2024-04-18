# -*- coding: utf-8 -*-

##############################################################################
#    Copyright (C) Ioppolo and Associates (I&A) 2023 (<http://ioppolo.com.au>).
###############################################################################

{
    "name": "MRP Sale",
    "summary": "Adds sale information to Manufacturing models",
    "version": "17.0.1.0.0",
    "category": "Manufacturing",
    "website": "http://www.ioppolo.com.au/",
    "author": "Ioppolo & Associates",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base",
        "mrp",
        "sale_stock",
        "ia_master_data",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/mrp_production_views.xml",
        "views/mrp_production_schedule_views.xml",
        "views/mrp_workorder_views.xml",
        "views/mrp_workcenter_views.xml",
        'views/sale_order_views.xml',
        'views/product_views.xml',
    ],
}
