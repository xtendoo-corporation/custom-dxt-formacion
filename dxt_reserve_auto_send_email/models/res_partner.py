from odoo import fields, models, api
import stdnum
from stdnum.eu.vat import check_vies
from stdnum.exceptions import InvalidComponent
from stdnum.util import clean

class ResPartner(models.Model):
    _inherit = "res.partner"

    tutor_signature = fields.Image('Firma tutor', copy=False,
                                     attachment=True,
                                     max_width=1024, max_height=1024)

    @api.depends("zip_id")
    def _compute_city_id(self):
        if self.env.context.get('no_vat_validation'):
            return
        if hasattr(super(), "_compute_city_id"):
            return
        for record in self:
            if record.zip_id:
                record.city_id = record.zip_id.city_id
            elif not record.country_enforce_cities:
                record.city_id = False

    def _fix_vat_number(self, vat, country_id):
        if self.env.context.get('no_vat_validation'):
            return vat
        code = self.env['res.country'].browse(country_id).code if country_id else False
        vat_country, vat_number = self._split_vat(vat)
        if code and code.lower() != vat_country:
            return vat
        stdnum_vat_fix_func = getattr(stdnum.util.get_cc_module(vat_country, 'vat'), 'compact', None)
        format_func_name = 'format_vat_' + vat_country
        format_func = getattr(self, format_func_name, None) or stdnum_vat_fix_func
        if format_func:
            vat_number = format_func(vat_number)
        return vat_country.upper() + vat_number






