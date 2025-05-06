from odoo import fields, models, api
from jinja2 import Template
import uuid
from odoo.addons.phone_validation.tools import phone_validation
from odoo.exceptions import UserError, AccessError
from datetime import datetime


class Lead(models.Model):
    _name = "crm.lead"
    _inherit = ['portal.mixin', 'crm.lead']

    student_signature = fields.Image('Signature', help='Signature received through the portal.', copy=False,
                                     attachment=True,
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

    product_id = fields.Many2one('product.template', string='Producto', )

    is_data_completed = fields.Boolean(string='Datos completos', default=False)

    def show_date_birth(self, date):
        date = date.strftime('%d/%m/%Y')
        return date

    def convert_date_to_datetime(self):
        if self.partner_id and self.partner_id.date_birth:
            date = self.partner_id.date_birth.strftime('%m/%d/%Y %I:%M %p')
        else:
            date = ''
        return date

    def get_tutor(self):
        if self.partner_id and self.partner_id.tutor:
            return self.partner_id.tutor
        return ''
    def get_acept_sepa(self):
        if self.partner_id and self.partner_id.accept_sepa:
            print("*"*100)
            print("aceppt_sepa", self.partner_id.accept_sepa)
            print("*"*100)
            if self.partner_id.accept_sepa:
                return 'Si'
            else:
                return 'No'
        return ''
    def get_acept_sepa_boolean(self):
        if self.partner_id and self.partner_id.accept_sepa:
            return self.partner_id.accept_sepa
        return False

    def get_state_name(self, state_id):
        state = self.env['res.country.state'].search([('id', '=', state_id)])
        if not state:
            return ''
        return state.name

    def get_country_name(self, country_id):
        country = self.env['res.country'].search([('id', '=', country_id)])
        if not country:
            return ''
        return country.name

    def get_state_selected(self):
        if self.partner_id and self.partner_id.state_id:
            return self.partner_id.state_id.id
        return self.env['res.country.state'].search([('name', '=', 'Sevilla')]).id

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        if self.stage_id:
            if self.stage_id.name == 'Reservado':
                self.send_email_reservado()
            elif self.stage_id.name == 'Informado':
                if not self.product_id:
                    raise UserError("Por favor, seleccione un producto.")
                if not self.product_id.is_published:
                    raise UserError("Por favor, seleccione un producto publicado en la web.")
                self.send_email_informado()

    def send_email_reservado(self):
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
            subject = f"DXT Formación Deportiva. {self.contact_name}, finaliza tu inscripción"
        else:
            subject = "DXT Formación Deportiva. Finaliza tu inscripción"

        mail_id = mail_obj.create({
            'email_from': self.user_id.email_formatted,
            'reply_to': self.user_id.email_formatted,
            'email_to': email_to,
            'subject': subject,
            'body_html': rendered_template_body,
            'is_notification': True,
            'model': 'crm.lead',
            'res_id': self_id,
            'body': rendered_template_body,
        })
        return True
    def send_email_informado(self):
        template = self.env.ref('dxt_reserve_auto_send_email.email_template_crm_lead_informado')
        self_id = str(self.id)
        partes = self_id.split("_")
        self_id = partes[-1]
        self_id = int(self_id)
        product_url = self._get_product_url(self.product_id.website_url)
        if not product_url:
            raise UserError("Por favor, configure El parámetro del sistema web.base.url.")
        template_values = {
            'object': self,
            'object_name': self.contact_name,
            'object_id': self_id,
            'product_url': product_url,
            'base_url': self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
        }
        template_body = template.body_html
        rendered_template_body = Template(template_body).render(template_values)

        mail_obj = self.env['mail.mail']
        email_to = self.email_from
        if self.contact_name:
            subject = f"DXT Formación Deportiva. {self.contact_name}, Reserva tu plaza"
        else:
            subject = "DXT Formación Deportiva. Reserva tu plaza"

        mail_id = mail_obj.create({
            'email_from': self.user_id.email_formatted,
            'reply_to': self.user_id.email_formatted,
            'email_to': email_to,
            'subject': subject,
            'body_html': rendered_template_body,
            'is_notification': True,
            'model': 'crm.lead',
            'res_id': self_id,
            'body': rendered_template_body,
        })
        return True

    def _get_product_url(self, product_url):
        if not self.env['ir.config_parameter'].sudo().get_param('web.base.url'):
            return
        return self.env['ir.config_parameter'].sudo().get_param('web.base.url') + product_url

    def _get_portal_form_return_action(self):
        """ Return the action used to display orders when returning from customer portal. """
        self.ensure_one()
        return self.env.ref('dxt_reserve_auto_send_email.portal_my_leads_form')

    def _get_data_complete_url(self, access_token):
        """ Return the action used to display orders when returning from customer portal. """
        self.ensure_one()
        return '/my/leads/%s?access_token=%s' % (self.id, access_token)

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
        # self.ensure_one()
        # if self.partner_id and self.phone != self.partner_id.phone:
        #     lead_phone_formatted = self.phone_get_sanitized_number(number_fname='phone') or self.phone or False
        #     partner_phone_formatted = self.partner_id.phone_get_sanitized_number(
        #         number_fname='phone') or self.partner_id.phone or False
        #     return lead_phone_formatted != partner_phone_formatted
        # return False
        return True

    @api.depends('phone', 'country_id.code')
    def _compute_phone_state(self):
        for lead in self:
            if self.env.user.name == 'Public user':
                lead.phone_state = 'correct'
            else:
                phone_status = False
                # if lead.phone:
                #     country_code = lead.country_id.code if lead.country_id and lead.country_id.code else None
                #     try:
                #         if phone_validation.phone_parse(lead.phone, country_code):  # otherwise library not installed
                #             phone_status = 'correct'
                #     except UserError:
                #         phone_status = 'incorrect'
                # lead.phone_state = phone_status
