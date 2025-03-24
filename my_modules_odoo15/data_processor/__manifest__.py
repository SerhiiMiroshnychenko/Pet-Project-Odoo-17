{
    "name": "Data Processor",
    "summary": "Module for customer data analysis",
    "description": """
Data Processor
==============================
This module analyzes customer data and creates visualizations
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
        "views/data_processor_views.xml",
        "views/menu_views.xml",
    ],
    "external_dependencies": {
        "python": ["matplotlib"],
    },
    "installable": True,
    "auto_install": False,
    "application": True,
}
