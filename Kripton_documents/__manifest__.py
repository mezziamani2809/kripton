# -*- coding:utf-8 -*-

{
    'name': 'Odoo 15 HR Documents',
    'category': 'Generic Modules/Human Resources',
    'version': '15.0.4.0.0',
    'sequence': 1,
    'author': 'Kripton',
    'summary': 'Documents For Odoo 15 Community Edition',
    'description': "Odoo 15 Documents, Documents Odoo 15, Odoo Community Documents",
    'license': 'LGPL-3',
    'depends': ['base', 'hr'],

    'data': [
        'security/ir.model.access.csv',
        'data/mail_data.xml',
        'views/documents_view.xml',

    ],
    'images': ['static/description/icon.png'],
    'application': True,
}
