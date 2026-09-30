#kripton@2023

{
    "name": "Kripton Invoicing V15",
    "description": """Kripton Invoicing V15""",
    "summary": "Kripton Invoicing V15",
    "category": "sales",
    "version": "15.0.0.0.0",
    'author': 'kripton',
    'company': 'kripton',
    'maintainer': 'kripton',
    'website': "http://www.kripton.fr",
    "depends": ['account', 'l10n_de','account_invoice_start_end_dates'],
    "data": [
        'security/ir.model.access.csv',
        'wizard/attachment_view.xml',
        'data/data_account_journal.xml',
        'report/report_invoice_document.xml',
        'views/account_move.xml',
        'views/gutschrift.xml',

    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
