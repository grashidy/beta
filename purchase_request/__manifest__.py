# -*- coding: utf-8 -*-
{
    'name': "Zad Purchase Request",
    'summary': """
    """,
    'description': """
    """,
    'author': "ZAD Solutions",
    'contributors': [
        'Ghada <grashidy@zadsolutions.com>',
    ],
    'version': '0.1',
    'depends': ['purchase', 'product', 'mail', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        "report/purchase_request_report.xml",
        "report/report.xml",
        'wizard/purchase_rejection_reason.xml',
        'views/purchase_request.xml',
        'views/purchase_order.xml',

    ],
    "pre_init_hook": None,
    "post_init_hook": None,
}
