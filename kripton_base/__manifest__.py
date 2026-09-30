# kripton@2023

{
    "name": "Kripton Base V15",
    "description": """Kripton Base V15""",
    "summary": "Kripton Base V15",
    "category": "Base",
    "version": "15.0.0.0.0",
    'author': 'kripton',
    'company': 'kripton',
    'maintainer': 'kripton',
    'website': "http:/www.kripton.fr",
    "depends": ["base", "hr", "sale","contacts","calendar"],
    "data": [
        'security/ir.model.access.csv',
        'views/res_partner.xml',
        'views/hr_employee.xml',
        'views/res_company.xml',
        'views/cost_employee.xml',

    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
