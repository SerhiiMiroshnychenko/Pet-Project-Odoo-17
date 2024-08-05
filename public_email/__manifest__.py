{
    'name': "Public Email",
    'summary': """
       Email Customization
    """,
    'description': """
      Public Email Customization

    """,
    'version': '17.0.1.0.0',
    "author": "Serhii Miroshnychenko",
    "website": "https://github.com/SerhiiMiroshnychenko",
    'license': "AGPL-3",
    'depends': [
        'mail',
        'helpdesk',
    ],
    'data': [
        'views/mail_compose_message_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'public_email/static/src/**/*',
        ],
    },

    'application': False,
    'installable': True,
    'auto_install': False,
}
