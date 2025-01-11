################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2024 Serhii Miroshnychenko (https://github.com/SerhiiMiroshnychenko).
#
################################################################################

{
    "name": "Customer Success Prediction",
    "summary": "Predict customer success rate based on historical data",
    "description": """
Customer Success Prediction
==============================
This module adds customer success prediction functionality:
        * Customer analytics dashboard
        * Historical sales analysis
        * Success rate prediction
        * Customer activity visualization
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
        "views/res_partner_views.xml",
        "views/data_collection_views.xml",
        "views/menu_views.xml",
        "views/partner_analysis_views.xml",
    ],
    "assets": {},
    "external_dependencies": {
        "python": ["matplotlib"],
    },
    "installable": True,
    "auto_install": False,
    "application": True,
}