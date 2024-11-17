################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2024 Serhii Miroshnychenko (https://github.com/SerhiiMiroshnychenko).
#
################################################################################

{
    'name': 'Product Analysis',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Product stock analysis tools',
    'description': """
        Module for analyzing product metrics including stock history.
    """,
    'author': "Serhii Miroshnychenko",
    'website': "https://github.com/SerhiiMiroshnychenko",
    'depends': ['product', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/stock_history_plot_wizard.xml',
        'views/product_views.xml',
    ],
    "assets": {
        "web.assets_frontend": [],
        "web.assets_backend": [
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    'external_dependencies': {
        'python': [
            'matplotlib',
            'numpy',
        ],
    },
}
