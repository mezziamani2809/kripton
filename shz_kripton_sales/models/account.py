# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, float_round
from odoo.exceptions import UserError


class account(models.Model):
    _inherit = 'account.move'

    po_id = fields.Many2one('sale.po', string='PO')

    def action_post(self):
        if self.po_id:
            if self.amount_untaxed > self.po_id.po_balance:
                raise ValidationError(
                    'You cannot post this invoice because the total amount is greater than the po balance amount.')
        return super(account, self).action_post()
