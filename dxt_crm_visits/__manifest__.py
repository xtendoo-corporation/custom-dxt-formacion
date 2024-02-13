# Copyright 2022 Xtendoo

{
    "name": "DXT CRM Visits",
    "summary": """
        Modify views CRM Visits""",
    "version": "15.0",
    "depends": ["crm"],
    "maintainers": ["dariocruzmauro"],
    "author": "Xtendoo",
    "license": "AGPL-3",
    "data": [
        "security/ir.model.access.csv",
        "views/crm_lead_view.xml",
        "views/place.xml"
            ],
    "installable": True,
    "auto_install": True,
}

