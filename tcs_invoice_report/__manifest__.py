# -*- coding: utf-8 -*-

{
    'name': "TCS Invoice Report",
    'version': '15.0.1.0.0',
    'summary': 'This app allows us to print TCS Invoices.',
    'description': 'This app allows us to print TCS Invoices.',
    'category': 'Extra Tools',
    'author': 'Kripton',
    'maintainer': 'Kripton',
    'company': 'Kripton',
    'depends': ['base', 'account'],
    'data': [
        'data/report_paperformat_data.xml',
        'report/tcs_report.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
