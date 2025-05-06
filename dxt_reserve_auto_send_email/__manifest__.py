# Copyright 2022 Xtendoo
{
    "name": "Dxt Reserve Auto Send Email",
    "summary": """
        Dxt Reserve Auto Send Email""",
    "version": "15.0",
    "depends": ["crm", "website", "dxt_crm_view", "web", "base_location"],
    "maintainers": ["Dani Domínguez"],
    "author": "Xtendoo",
    "license": "AGPL-3",
    "data": [
        "data/mail_template.xml",
        "views/portal_view.xml",
        "views/crm_lead.xml",

    ],
    "installable": True,
    "auto_install": True,
}



