################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2024 Serhii Miroshnychenko (https://github.com/SerhiiMiroshnychenko).
#
################################################################################

{
    "name": "Styling",
    "summary": "A module for Odoo stylization",
    "description": """
Styling
=============================
A module for Odoo stylization
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
        'views/styling_menu_views.xml',
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
