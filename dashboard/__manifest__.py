# -*- coding: utf-8 -*-
{
    "name": "Dashboard",
    "version": "15.0.1.0.1",
    "summary": """ 
            Dashboard
            .""",
    "description": """ 
            Dashboard
            .""",
    "author": "Kriptix",
    "company": "Kriptix",
    "maintainer": "Kriptix",
    "images": ["static/description/icon.png"],
    "license": "LGPL-3",
    "installable": True,
    "application": True,
    "auto_install": False,
    "depends": ["hr", 'account', "kripton_base","web"],
    "data": [
        "views/dashboard_view.xml",
    ],
    'assets': {
        'web.assets_backend': [
            'https://cdn.jsdelivr.net/npm/chart.js',
            'dashboard/static/src/js/dashboard.js',
        ],
        'web.assets_qweb': [
            'dashboard/static/src/xml/dashboard.xml',
        ],
    },
}
