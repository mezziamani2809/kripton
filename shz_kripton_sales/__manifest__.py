# kripton@2023

{
    "name": "SHZ Kripton Sales V15",
    "description": """Sales V15""",
    "summary": "Kripton Sales V15",
    "category": "sales",
    "version": "15.0.0.0.0",
    'author': 'Shazler ERP',
    'company': 'Shazler',
    'maintainer': 'kripton',
    'website': "shazler.com",
    "depends": ['sale', 'account', 'sale_management', 'kripton_base', 'sale_purchase', 'sale_project', 'project','shz_contract_client','account_invoice_start_end_dates'],
    "data": [
        'security/ir.model.access.csv',
        'views/sale_order.xml',
        'views/po_sale.xml',
        'views/account_move_views.xml',
        'views/sale_make_invoice_advance_views.xml',
        'wizard/end_contract_wizard.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
