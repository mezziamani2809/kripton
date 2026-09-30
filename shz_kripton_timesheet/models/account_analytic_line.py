# Odoo Module: Your Module Name
# Description: This module extends the functionality of account.analytic.line and project.task models.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    _description = 'Analytic Line'

