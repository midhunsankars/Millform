# -*- coding: utf-8 -*-
{
    "name": "External Database Sources",
    "version": "17.0.1.0.0",
    "category": "Tools",
    "author": "Ioppolo & Associates",
    "website": "http://www.ioppolo.com.au/",
    "license": "LGPL-3",
    "depends": ["base"],
    "external_dependencies": {
        "python": ["sqlalchemy"]
    },
    "data": [
        "views/base_external_dbsource.xml",
        "security/ir.model.access.csv",
        "security/base_external_dbsource_security.xml",
    ],
    "installable": True,
}
