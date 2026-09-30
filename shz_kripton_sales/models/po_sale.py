# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, float_round
from odoo.exceptions import UserError


class SaleOrder_po(models.Model):
    _name = 'sale.po'
    _description = 'Purchase Orders - PO'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'client_order_ref'

    client_order_ref = fields.Char(string='Contract Number', copy=False, default='NEW')
    sale_id = fields.Many2one('sale.order', 'Sale Order')
    currency_id = fields.Many2one('res.currency', related="sale_id.currency_id", string="Currency")
    timesheets_attachment_po = fields.Binary(string="Purchase Order (PO)")
    date_po = fields.Date('Start Date PO', required=False, index=True, default=fields.Date.context_today)
    end_date_po = fields.Date('End Date PO', required=False, index=True)
    po_amount = fields.Monetary(string='PO amount')
    po_balance = fields.Monetary(string='PO Balance', compute="_compute_invoice_amount_total", store=True)
    quantity_by_day = fields.Float('PO Volume')
    number_of_hour_by_day = fields.Integer('PO', default=8.0)
    totol_hours = fields.Integer('PO Volume ')

    contract_type = fields.Selection([
        ('d', 'Days'),
        ('h', 'Hour'),
    ], string="PO unit")
    invoice_payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms')
    move_ids = fields.One2many('account.move', 'po_id')
    invoice_count = fields.Integer(compute='_compute_invoice_count', string="Invoice Count")

    @api.depends('move_ids.amount_untaxed_signed', 'move_ids.state', 'po_amount')
    def _compute_invoice_amount_total(self):
        for order in self:
            # Filtrer uniquement les factures validées (state='posted')
            invoices = order.move_ids.filtered(lambda inv: inv.state == 'posted')
            order.po_balance = order.po_amount - sum(invoices.mapped('amount_untaxed_signed'))

    @api.depends('move_ids')
    def _compute_invoice_count(self):
        for po in self:
            po.invoice_count = len(po.move_ids)

    def action_view_invoices(self):
        self.ensure_one()
        return {
            'name': _('Invoices'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            # 'view_id': self.env.ref('account.view_out_invoice_tree').id,
            'res_model': 'account.move',
            'domain': [('po_id', '=', self.id)],
            'context': {
                'default_po_id': self.id,
                'default_move_type': 'out_invoice',
                'create': False,
                'delete': False,
                'duplicate': False,
            },
        }

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        move_id = self._context.get('filter_po_by_move')
        if move_id:
            move = self.env['account.move'].browse(move_id)
            sale_orders = move.invoice_line_ids.mapped('sale_line_ids.order_id')
            print('sale_orders', sale_orders, move.amount_total)

            valid_pos = self.env['sale.po'].search([
                ('id', 'in', sale_orders.po_ids.ids),
                ('po_balance', '>', 0),
                ('po_balance', '>=', move.amount_total)])

            print('valid_pos', valid_pos)
            args += [('id', 'in', valid_pos.ids)]
        return super(SaleOrder_po, self).name_search(name=name, args=args, operator=operator, limit=limit)
