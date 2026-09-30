# -*- coding: utf-8 -*-
{
    'license': 'LGPL-3',
    'name': "Document Management System",
    'summary': "Enterprise online document management",
    'author': "renjie <i@renjie.me>",
    'website': "https://renjie.me",
    'support': 'i@renjie.me',
    'category': 'Document Management',
    'version': '1.0',
    'depends': ['mail'],
    'data': [
        'security/account_security.xml',
        'security/ir.model.access.csv',
        'wizard/multi_attachment_view.xml',
        'data/ir_sequence_data.xml',
        'data/ir_cron.xml',
        'data/data_accounting_old.xml',
        'data/data_accounting_2025_old.xml',
        'data/data_accounting_2024.xml',
        'data/data_accounting_2025.xml',
        'views/document.xml',
        'views/bi_lead.xml',

    ],
    'images': [
        'static/description/main_screenshot.png',
    ],
    'assets': {
        'web.assets_backend': [
            'document_management_system/static/src/**/*.scss',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
}
