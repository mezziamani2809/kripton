# -*- coding: utf-8 -*-
###############################################################################
{
    'name': 'Due Date Reminder for Invoicing',
    'version': '15.0..0.0',
    'category': 'Sales, Accounting',
    'summary': """Send reminder mail for all the partners with due on invoicing.""",
    'description': """This module crafted by kriptix provides 
                      an option to send reminder mail for all the partners 
                      with due on sale order and invoicing.By using scheduled 
                      action, it will send reminder mail in the exact time.""",
    'author': 'kriptix',
    'company': 'kriptix',
    'maintainer': 'kriptix',
    'images': ['static/description/banner.png'],
    'depends': ['base', 'sale_management', 'account'],
    'data': [
        'data/mail_data.xml',
        'data/ir_cron_data.xml',
        'views/res_config_settings_views.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
