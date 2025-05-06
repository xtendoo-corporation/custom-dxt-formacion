# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re

from odoo import api, fields, models, _
from odoo.addons.phone_validation.tools import phone_validation
from odoo.exceptions import AccessError, UserError
from odoo.osv import expression


class PhoneMixin(models.AbstractModel):
    _inherit = 'mail.thread.phone'

    @api.depends(lambda self: self._phone_get_sanitize_triggers())
    def _compute_phone_sanitized(self):
        if self.env.user.name == 'Public user':
            return
        if self.env.context.get('no_vat_validation'):
            return
        self._assert_phone_field()
        number_fields = self._phone_get_number_fields()
        # for record in self:
        #     for fname in number_fields:
                # sanitized = record.phone_get_sanitized_number(number_fname=fname)
                # if sanitized:
                #     break
            # record.phone_sanitized = sanitized

class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _prepare_tracking(self, fields):
        if self.env.context.get('no_tracking'):
            return
        """ Prepare the tracking of ``fields`` for ``self``.

        :param fields: iterable of fields names to potentially track
        """
        fnames = self._get_tracked_fields().intersection(fields)
        if not fnames:
            return
        self.env.cr.precommit.add(self._finalize_tracking)
        initial_values = self.env.cr.precommit.data.setdefault(f'mail.tracking.{self._name}', {})
        for record in self:
            if not record.id:
                continue
            values = initial_values.setdefault(record.id, {})
            if values is not None:
                for fname in fnames:
                    values.setdefault(fname, record[fname])

