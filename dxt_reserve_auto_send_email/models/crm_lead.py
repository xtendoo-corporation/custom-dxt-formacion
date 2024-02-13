from odoo import fields, models, api
from jinja2 import Template
import uuid
from odoo.addons.phone_validation.tools import phone_validation
from odoo.exceptions import UserError, AccessError

class Lead(models.Model):
    _name = "crm.lead"
    _inherit = ['portal.mixin','crm.lead']

    student_signature = fields.Image('Signature', help='Signature received through the portal.', copy=False, attachment=True,
                             max_width=1024, max_height=1024)
    student_signed_by = fields.Char('Signed By', help='Name of the person that signed the SO.', copy=False)
    student_signed_on = fields.Datetime('Signed On', help='Date of the signature.', copy=False)

    tutor_signature = fields.Image('Signature', help='Signature received through the portal.', copy=False,
                                     attachment=True,
                                     max_width=1024, max_height=1024)
    tutor_signed_by = fields.Char('Signed By', help='Name of the person that signed the SO.', copy=False)
    tutor_signed_on = fields.Datetime('Signed On', help='Date of the signature.', copy=False)

    access_token = fields.Char(string="Access Token", default=lambda self: str(uuid.uuid4()),
                               groups='base.group_system', required=True, readonly=True, copy=False)

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        if self.stage_id:
            if self.stage_id.name == 'Reservado':
                self.send_email()

    def send_email(self):
        template = self.env.ref('dxt_reserve_auto_send_email.email_template_crm_lead')
        self_id = str(self.id)
        partes = self_id.split("_")
        self_id = partes[-1]
        self_id = int(self_id)
        template_values = {
            'object': self,
            'object_name': self.name,
            'object_id': self_id,
            'access_token': self.access_token,
        }
        template_body = template.body_html
        rendered_template_body = Template(template_body).render(template_values)

        mail_obj = self.env['mail.mail']
        email_to = self.email_from
        if self.contact_name:
            subject = f"DXT Fomación Deportiva. {self.contact_name}, finaliza tu inscripción"
        else:
            subject = "DXT Fomación Deportiva. Finaliza tu inscripción"

        mail_id = mail_obj.create({
            'email_from': self.user_id.email_formatted,
            'email_to': email_to,
            'subject': subject,
            'body_html': rendered_template_body,
        })
        mail_obj.send(mail_id)
        return True

    def _get_portal_form_return_action(self):
        """ Return the action used to display orders when returning from customer portal. """
        self.ensure_one()
        return self.env.ref('dxt_reserve_auto_send_email.portal_my_leads_form')

    def _get_student_sign_url(self, lead_id, access_token):
        """ Return the action used to display orders when returning from customer portal. """
        self.ensure_one()
        return '/my/leads/%s/accept_student?access_token=%s' % (lead_id.id, access_token)

    def _get_tutor_sign_url(self, lead_id, access_token):
        """ Return the action used to display orders when returning from customer portal. """
        self.ensure_one()
        return '/my/leads/%s/accept_tutor?access_token=%s' % (lead_id.id, access_token)


    def get_portal_url(self, suffix=None, report_type=None, download=None, query_string=None, anchor=None):
        """
            Get a portal url for this model, including access_token.
            The associated route must handle the flags for them to have any effect.
            - suffix: string to append to the url, before the query string
            - report_type: report_type query string, often one of: html, pdf, text
            - download: set the download query string to true
            - query_string: additional query string
            - anchor: string to append after the anchor #
        """
        self.ensure_one()
        url = self.access_url + '%s?access_token=%s%s%s%s%s' % (
            suffix if suffix else '',
            self._portal_ensure_token(),
            '&report_type=%s' % report_type if report_type else '',
            '&download=true' if download else '',
            query_string if query_string else '',
            '#%s' % anchor if anchor else ''
        )
        return url

    def _get_portal_return_action(self):
        """ Return the action used to display orders when returning from customer portal. """
        self.ensure_one()
        return self.env.ref('dxt_reserve_auto_send_email.lead_confirm_data_template')

    def _get_states(self):
        self.ensure_one()
        return self.env['res.country.state'].sudo().search([('country_id.code', '=', 'ES')])

    def _get_countries(self):
        self.ensure_one()
        return self.env['res.country'].sudo().search([('code', '=', 'ES')])

    def has_to_be_signed_student(self):
        return not self.student_signature

    def has_to_be_signed_tutor(self):
        return not self.tutor_signature

    def _get_partner_phone_update(self):
        if self.env.user.name == 'Public user':
            return
        self.ensure_one()
        if self.partner_id and self.phone != self.partner_id.phone:
            lead_phone_formatted = self.phone_get_sanitized_number(number_fname='phone') or self.phone or False
            partner_phone_formatted = self.partner_id.phone_get_sanitized_number(number_fname='phone') or self.partner_id.phone or False
            return lead_phone_formatted != partner_phone_formatted
        return False

    @api.depends('phone', 'country_id.code')
    def _compute_phone_state(self):
        for lead in self:
            if self.env.user.name == 'Public user':
                lead.phone_state = 'correct'
            else:
                phone_status = False
                if lead.phone:
                    country_code = lead.country_id.code if lead.country_id and lead.country_id.code else None
                    try:
                        if phone_validation.phone_parse(lead.phone, country_code):  # otherwise library not installed
                            phone_status = 'correct'
                    except UserError:
                        phone_status = 'incorrect'
                lead.phone_state = phone_status
