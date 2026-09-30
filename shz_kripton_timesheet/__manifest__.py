#kripton@2023

{
    "name": " shz Kripton Timesheets V15",
    "description": """ shz Kripton Timesheets V15""",
    "summary": "Kripton Timesheets V15",
    "category": "Timesheets",
    "version": "15.0.0.0.0",
    'author': 'shazler',
    'company': 'shazler',
    'website': "shazler.com",
    "depends": ['kripton_timesheet','shz_kripton_sales'],
    "data": [
        # 'data/mail_data.xml',
        'views/account_analytic_line.xml',
        # 'views/add_timesheet_view.xml',
        # 'security/ir.model.access.csv',
        # 'wizard/multi_attachment_view.xml',
    ],

    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
