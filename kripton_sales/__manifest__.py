#kripton@2023

{
    "name": "Kripton Sales V15",
    "description": """Kripton Sales V15""",
    "summary": "Kripton Sales V15",
    "category": "sales",
    "version": "15.0.0.0.0",
    'author': 'kripton',
    'company': 'kripton',
    'maintainer': 'kripton',
    'website': "http://www.kripton.fr",
    "depends": ['sale', "kripton_base",'sale_purchase','sale_project','project'],
    "data": [
        'security/ir_groups.xml',
        'views/sale_order.xml',
        'views/services_view.xml',
        'views/payment_term.xml',

    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
