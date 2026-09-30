# -*- coding: utf-8 -*-
###############################################################################
{
    'name': 'Time Off Reminder',
    'version': '15.0..0.0',
    'category': 'Time Off',
    'summary': """Send Time Off Reminder""",
    'description': """This module crafted by kriptix provides 
                      an option to send reminder mail Time Off Reminder.""",
    'author': 'kriptix',
    'company': 'kriptix',
    'maintainer': 'kriptix',
    'images': ['static/description/banner.png'],
    'depends': ['hr'],

    'data': [
        'data/mail_data.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
