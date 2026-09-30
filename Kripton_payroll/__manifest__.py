# -*- coding:utf-8 -*-

{
    'name': 'Odoo 15 HR Payroll',
    'category': 'Generic Modules/Human Resources',
    'version': '15.0.4.0.0',
    'sequence': 1,
    'author': 'Kripton',
    'summary': 'Payroll For Odoo 15 Community Edition',
    'description': "Odoo 15 Payroll, Payroll Odoo 15, Odoo Community Payroll",
    'license': 'LGPL-3',
    'depends': ['base', 'hr'],

    'data': [
        'security/ir.model.access.csv',
        'views/payroll_view.xml',

    ],
    'images': ['static/description/icon.png'],
    'application': True,
}
