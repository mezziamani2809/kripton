#kripton@2023

{
    "name": "Kripton Timesheets V15",
    "description": """Kripton Timesheets V15""",
    "summary": "Kripton Timesheets V15",
    "category": "Timesheets",
    "version": "15.0.0.0.0",
    'author': 'kripton',
    'company': 'kripton',
    'maintainer': 'kripton',
    'website': "http://www.kripton.fr",
    "depends": ["hr_timesheet",'sale'],
    "data": [
        'data/mail_data.xml',
        'views/account_analytic_line.xml',
        'views/add_timesheet_view.xml',
        'security/ir.model.access.csv',
        'wizard/multi_attachment_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'kripton_timesheet/static/src/js/list_view_button.js',
        ],
        'web.assets_qweb': [
            'kripton_timesheet/static/src/xml/list_view_button.xml',

        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
