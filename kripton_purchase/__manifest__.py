#kripton@2023

{
    "name": "Kripton Purchase V15",
    "description": """Kripton Purchase V15""",
    "summary": "Kripton Purchase V15",
    "category": "Purchase",
    "version": "15.0.0.0.0",
    'author': 'kripton',
    'company': 'kripton',
    'maintainer': 'kripton',
    'website': "http://www.kripton.fr",
    'depends': ['base','purchase','sale','sale_management','hr'],
    "data": [
        'views/purchase_view.xml',
        'views/inherit_purchase_report.xml',
        'report/contracts_report.xml',

    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
