# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import binascii
from odoo import fields, http, SUPERUSER_ID, _
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.http import request
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers import portal
from datetime import datetime

class CustomerPortal(portal.CustomerPortal):

    @http.route(['/my/leads/<int:lead_id>/accept_tutor'], type='json', auth="public", website=True)
    def portal_tutor_signature(self, lead_id, access_token=None, name=None, signature=None):
        access_token = access_token or request.httprequest.args.get('access_token')
        try:
            lead_sudo = self._document_check_access('crm.lead', lead_id, access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Invalid lead.')}

        if not signature:
            return {'error': _('Signature is missing.')}

        try:
            lead_sudo.write({
                'tutor_signed_by': name,
                'tutor_signed_on': fields.Datetime.now(),
                'tutor_signature': signature,
            })
            request.env.cr.commit()
        except (TypeError, binascii.Error) as e:
            return {'error': _('Invalid signature data.')}
        url = '/my/leads/%s?access_token=%s' % (lead_id, access_token)
        return {
            'force_refresh': True,
            'redirect_url': url,
        }

    @http.route(['/my/leads/<int:lead_id>/accept_student'], type='json', auth="public", website=True)
    def portal_student_signature(self, lead_id, access_token=None, name=None, signature=None):
        # get from query string if not on json param
        access_token = access_token or request.httprequest.args.get('access_token')
        try:
            lead_sudo = self._document_check_access('crm.lead', lead_id, access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Invalid lead.')}

        if not signature:
            return {'error': _('Signature is missing.')}

        try:
            lead_sudo.write({
                'student_signed_by': name,
                'student_signed_on': fields.Datetime.now(),
                'student_signature': signature,
            })
            request.env.cr.commit()
        except (TypeError, binascii.Error) as e:
            return {'error': _('Invalid signature data.')}
        url = '/my/leads/%s?access_token=%s' % (lead_id, access_token)
        return {
            'force_refresh': True,
            'redirect_url': url,
        }

    @http.route(['/form/leads/<int:lead_id>'], type='http', auth="public", website=True)
    def portal_lead_form(self, lead_id, report_type=None, access_token=None, message=False, download=False, **kw):
        try:
            lead_sudo = self._document_check_access('crm.lead', lead_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if lead_sudo:
            now = fields.Date.today().isoformat()
            session_obj_date = request.session.get('view_lead_%s' % lead_sudo.id)
            if session_obj_date != now and request.env.user.share and access_token:
                request.session['view_lead_%s' % lead_sudo.id] = now
                body = _('Lead viewed by customer %s',
                         lead_sudo.partner_id.name if request.env.user._is_public() else request.env.user.partner_id.name)
                _message_post_helper(
                    "crm.lead",
                    lead_sudo.id,
                    body,
                    token=lead_sudo.access_token,
                    message_type="notification",
                    subtype_xmlid="mail.mt_note",
                    partner_ids=lead_sudo.user_id.sudo().partner_id.ids,
                )

        values = {
            'lead': lead_sudo,
            'message': message,
            'token': access_token,
            'bootstrap_formatting': True,
            'partner_id': SUPERUSER_ID,
            'report_type': 'html',
            'action': lead_sudo._get_portal_form_return_action(),

        }
        return request.render('dxt_reserve_auto_send_email.portal_my_leads_form', values)

    @http.route(['/my/leads/<int:lead_id>'], type='http', auth="public", website=True)
    def portal_lead_page(self, lead_id, access_token=None, message=False, **post):
        if post:
            self.update_student_data(post)
        try:
            lead_sudo = self._document_check_access('crm.lead', lead_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        if lead_sudo:
            now = fields.Date.today().isoformat()
            session_obj_date = request.session.get('view_lead_%s' % lead_sudo.id)
            if session_obj_date != now and request.env.user.share and access_token:
                request.session['view_lead_%s' % lead_sudo.id] = now
                body = _('Lead viewed by customer %s',
                         lead_sudo.partner_id.name if request.env.user._is_public() else request.env.user.partner_id.name)
                _message_post_helper(
                    "crm.lead",
                    lead_sudo.id,
                    body,
                    token=lead_sudo.access_token,
                    message_type="notification",
                    subtype_xmlid="mail.mt_note",
                    partner_ids=lead_sudo.user_id.sudo().partner_id.ids,
                )

        values = {
            'lead': lead_sudo,
            'message': message,
            'token': access_token,
            'bootstrap_formatting': True,
            'partner_id': SUPERUSER_ID,
            'report_type': 'html',
            'action': lead_sudo._get_portal_return_action(),

        }
        return request.render('dxt_reserve_auto_send_email.lead_confirm_data_template', values)

    def update_student_data(self, post):
        partner_name = post.get('name')
        partner = request.env['res.partner'].sudo().search([
                ('name', '=', partner_name),
            ])
        date_birth = post.get('date_birth')
        if date_birth:
            date_to_save = date_birth[6:10] + "/" + date_birth[0:2] + "/" + date_birth[3:5]
            date_birth = datetime.strptime(date_to_save, '%Y/%m/%d').date()
        if post.get('country_id'):
            country = request.env['res.country'].sudo().browse(post.get('country_id'))
            if not country:
                country = None
            else:
                country = country[0].id
        if post.get('state_id'):
            state = request.env['res.country.state'].sudo().browse(post.get('state_id'))
            if not state:
                state = None
            else:
                state = state[0].id
        if not partner:
            partner = request.env['res.partner'].with_context(no_vat_validation=True).sudo().create(
                {
                    'name': partner_name,
                    'email': post.get('email'),
                    'phone': post.get('phone'),
                    'country_id': country,
                    'street': post.get('street'),
                    'state_id': state,
                    'city': post.get('city'),
                    'zip': post.get('zip'),
                    'is_student': True,
                    'date_birth': date_birth,
                    'vat': post.get('vat'),
                    'tutor': post.get('tutor'),
                    'accept_sepa': post.get('accept_sepa'),
                    'bank_account': post.get('bank_account'),
                }
            )
        else:
            partner = partner[0]
            partner = partner.with_context(no_vat_validation=True)
            partner.sudo().write(
                {
                    'name': partner_name,
                    'email': post.get('email'),
                    'phone': post.get('phone'),
                    'country_id': country,
                    'street': post.get('street'),
                    'state_id': state,
                    'city': post.get('city'),
                    'zip': post.get('zip'),
                    'is_student': True,
                    'date_birth': date_birth,
                    'vat': post.get('vat'),
                    'tutor': post.get('tutor'),
                    'accept_sepa': post.get('accept_sepa'),
                    'bank_account': post.get('bank_account'),
                }
            )
        lead_to_write = request.env['crm.lead'].sudo().search([
                ('id', '=', int(post.get('lead'))),
            ])
        lead_to_write = lead_to_write[0]
        lead_to_write = lead_to_write.with_context(no_tracking=True)
        lead_to_write.sudo().write(
            {
                'partner_id': partner.id,
            }
        )

