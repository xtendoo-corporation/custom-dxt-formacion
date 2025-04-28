import re

from odoo import api, fields, models, _
from odoo.addons.crm.models import crm_stage
from bs4 import BeautifulSoup
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

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """ Overrides mail_thread message_new that is called by the mailgateway
            through message_process.
            This override updates the document according to the email.
        """
        self = self.with_context(default_user_id=False)

        if custom_values is None:
            custom_values = {}
        body = msg_dict.get('body', "")
        company_id = self.env['res.company'].search([('name', 'ilike', 'DXT Formacion Deportiva')], limit=1)
        team_id = self.env['crm.team'].search([('name', 'ilike', 'Ventas')], limit=1)
        extracted_data = self._extract_data_from_body(body)
        email_from = msg_dict.get('from')
        if extracted_data.get('email'):
            email_from = extracted_data.get('email')
        description_text=""
        if extracted_data.get('center'):
            description_text = f"Centro: {extracted_data.get('center')}<br>"
        if extracted_data.get('msg_txt'):
            description_text += f"Texto de mensaje:<br>"
            description_text += f"{self.format_text_with_breaks(extracted_data.get('msg_txt'))}<br>"
        if extracted_data.get('private_policy'):
            description_text += f"{extracted_data.get('private_policy')}"


        defaults = {
            'name': msg_dict.get('subject') or _("No Subject"),
            'email_from': email_from,
            'company_id': company_id.id,
            'phone': extracted_data.get('phone', False),
            'contact_name': extracted_data.get('name', False),
            'team_id': team_id.id,
            'description': description_text,
        }
        if msg_dict.get('priority') in dict(crm_stage.AVAILABLE_PRIORITIES):
            defaults['priority'] = msg_dict.get('priority')
        defaults.update(custom_values)

        return super(CrmLead, self).message_new(msg_dict, custom_values=defaults)

    def _extract_data_from_body(self, body):
        soup = BeautifulSoup(body, "html.parser")
        raw_text = soup.get_text(separator="\n")
        lines = raw_text.split("~")
        datos = {
            k.strip(): v.strip()
            for line in lines
            if ":" in line and len(line.split(":", 1)) == 2
            for k, v in [line.split(":", 1)]
        }

        return datos

    def format_text_with_breaks(self,text):
        return text.replace("\n", "<br>") if text else ""
