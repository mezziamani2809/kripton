# kripton@2023

{
    "name": "SHZ Base contact V15",
    "description": """SHZ Base contact V15""",
    "summary": "SHZ Base contact V15",
    "category": "Base",
    "version": "15.0.0.0.0",
    'author': 'Shazler ERP',
    'company': 'Shazler ERP',
    'maintainer': 'Shazler ERP',
    'website': "shazler.com",
    "depends": ["base", "kripton_sales", "kripton_timesheet"],
    "data": [
        'data/ir_cron.xml',
        'views/sale_order.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
