################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2024 Serhii Miroshnychenko (https://github.com/SerhiiMiroshnychenko).
#
################################################################################

{
    "name": "Chatter Buttons",
    "summary": "Some objects & business logic to add new Chatter buttons",
    "description": """
Chatter Buttons
==============================
A module to add new Chatter buttons
""",
    "version": "17.0.1.0.0",
    "author": "Serhii Miroshnychenko",
    "website": "https://github.com/SerhiiMiroshnychenko",
    "license": "OPL-1",
    "category": "Customizations",
    "depends": [
        "mail",
    ],
    "data": [
    ],
    "assets": {
        "web.assets_frontend": [],
        "web.assets_backend": [
            'chatter_button/static/src/**/*',
        ],
    },
    "external_dependencies": {},
    "installable": True,
    "auto_install": False,
    "application": True,
}
