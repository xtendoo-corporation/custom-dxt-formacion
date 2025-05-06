from odoo import fields, models

class ResPartner(models.Model):
    _inherit = "res.partner"

    is_student = fields.Boolean(
        string="Alumno",
    )
    ref_alexia = fields.Char(
        string="Id Alexia",
    )
    date_birth = fields.Date(
        string="Date of Birth",
    )
    tutor = fields.Char(
        string="Tutor",
    )
    bank = fields.Char(
        string="Bank",
    )
    bank_account = fields.Char(
        string="Bank account",
    )


