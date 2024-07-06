################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2024 Serhii Miroshnychenko (https://github.com/SerhiiMiroshnychenko).
#
################################################################################

{
    "name": "Odoo Improving",
    "summary": "Some objects & business logic to enhance Odoo functionality ",
    "description": """
Odoo Improving
==============================
A module to enhance Odoo functionality
""",
    "version": "17.0.1.0.0",
    "author": "Serhii Miroshnychenko",
    "website": "https://github.com/SerhiiMiroshnychenko",
    "license": "OPL-1",
    "category": "Customizations",
    "depends": [
        "crm",
    ],
    "data": [
        'views/imp_menu_views.xml',
        'views/crm_lead_views.xml',
    ],
    "assets": {
        "web.assets_frontend": [],
        "web.assets_backend": [
            '/mir_imp/static/src/css/*.css',
        ],
    },
    "external_dependencies": {},
    "installable": True,
    "auto_install": False,
    "application": True,
}
