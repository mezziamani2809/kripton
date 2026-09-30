# Copyright 2013-2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.misc import format_date


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    start_date = fields.Date(index=True, string='End Date Timesheets')
    end_date = fields.Many2one('res.partner', string='Consultant', force_save="1",index=True)
    must_have_dates = fields.Boolean(related="product_id.must_have_dates")


