# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, float_round
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'
    employees_ids = fields.One2many('hr.employee', 'user_partner_id', string='Employees', domain=[
        ('active', '=', True)])


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    po_ids = fields.One2many('sale.po', 'sale_id', string='Liste des PO')
    po_count = fields.Integer(compute='_compute_po_count', string="PO Count")

    @api.depends('po_ids')
    def _compute_po_count(self):
        for order in self:
            order.po_count = len(order.po_ids)

    def action_view_pos(self):
        self.ensure_one()
        return {
            'name': _('Purchase Orders'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'sale.po',
            'domain': [('sale_id', '=', self.id)],
            'context': {
                'default_sale_id': self.id,
                'create': False,
                'delete': False,
                'duplicate': False,
            },
        }

    partner_id = fields.Many2one(
        'res.partner', string='Client', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        required=True, change_default=True, index=True, tracking=1,
        domain="[('type', '!=', 'private'), ('company_id', 'in', (False, company_id))]", )

    def action_open_end_contract_wizard(self):
        return {
            'name': 'Contract End Date',
            'type': 'ir.actions.act_window',
            'res_model': 'contract.end.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sale_order_id': self.id},
        }