# -*- coding: utf-8 -*-

{
    'name': "Vendor Sequence Number",
    "version": "15.0.0.0",
    'author': 'PK Meta Code',
    'summary': 'Sequence number for Vendor',
    'license': 'LGPL-3',
    "description": """This module generate sequence number for vendor.""",
    'depends': ['base', 'sale_management', 'purchase'],
    'data': [
        'data/sequence.xml',
        'views/res_partner.xml',
    ],

    'images': ['static/description/banner.png'],
    "auto_install": False,
    "installable": True,

}
