################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2024 Serhii Miroshnychenko (https://github.com/SerhiiMiroshnychenko).
#
################################################################################

{
    "name": "Data Collector",
    "summary": "Module for historical data collection",
    "description": """
Data Collector
==============================
This module collects historical data
""",
    "version": "15.0.1.0.0",
    "author": "Serhii Miroshnychenko",
    "website": "https://github.com/SerhiiMiroshnychenko",
    "license": "OPL-1",
    "category": "Sales/CRM",
    "depends": [
        "sale_crm", "web",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/data_collection_views.xml",
        "views/menu_views.xml",
    ],
    "assets": {},
    "external_dependencies": {
        "python": ["matplotlib"],
    },
    "installable": True,
    "auto_install": False,
    "application": True,
}