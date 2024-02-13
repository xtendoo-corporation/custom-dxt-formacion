from odoo import api, fields, models

import logging

class PlaceVisit(models.Model):
    _name = 'place.visit'

    crm_lead_id = fields.One2many(
        comodel_name="crm.lead",
        required=True,
        inverse_name="place_visit_id",
    )
    name = fields.Char(
        string='Lugar',
    )

class CrmLead(models.Model):
    _inherit = "crm.lead"

    visit = fields.Boolean(
        default=False,
        string="Visita",
    )
    date_visit = fields.Datetime(
        string="Fecha y hora de visita",
    )
    place_visit_id = fields.Many2one(
        comodel_name="place.visit",
        string="Lugar de visita",
    )
