{
    "name": "Order Data Collector",
    "summary": "Module for collecting and analyzing sales order data",
    "description": """
Order Data Collector
==============================
This module collects and analyzes sales order data with focus on order success rates
""",
    "version": "15.0.1.0.0",
    "author": "Serhii Miroshnychenko",
    "website": "https://github.com/SerhiiMiroshnychenko",
    "license": "OPL-1",
    "category": "Sales/CRM",
    "depends": [
        "sale_crm",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/order_data_collector_views.xml",
        "views/menu_views.xml",
    ],
    "external_dependencies": {
        "python": ["pandas"],
    },
    "installable": True,
    "auto_install": False,
    "application": True,
}
