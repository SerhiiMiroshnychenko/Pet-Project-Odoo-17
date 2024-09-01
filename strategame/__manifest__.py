################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2024 Serhii Miroshnychenko (https://github.com/SerhiiMiroshnychenko).
#
################################################################################

{
    "name": "Strategame",
    "summary": "Strategic Game in Odoo",
    "description": """
Strategame
======================
Strategic Game in Odoo
""",
    "version": "17.0.1.0.0",
    "author": "Serhii Miroshnychenko",
    "website": "https://github.com/SerhiiMiroshnychenko",
    "license": "OPL-1",
    "category": "Extra Tools",
    "depends": [],
    "data": [
        "security/ir.model.access.csv",

        "views/homeland_views.xml",
        "views/game_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [],
        "web.assets_backend": [
            '/strategame/static/src/css/*.css',
        ],
    },
    "external_dependencies": {},
    "installable": True,
    "auto_install": False,
    "application": True,
}
