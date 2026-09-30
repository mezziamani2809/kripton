# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from xml import etree
from psycopg2 import sql, DatabaseError
from odoo.exceptions import ValidationError
from odoo import api, fields, models
from datetime import date
_logger = logging.getLogger(__name__)
class Sale0rder(models.Model):
    _inherit = 'sale.order'
    final_customer_id = fields.Many2one('res.partner', string="End Client")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Quotation Sent'),
        ('sale', 'In progress'),
        ('done', 'Expired'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')
    @api.model
    def create(self, vals):
        res = super(Sale0rder, self).create(vals)
        res._update_contract_state()
        return res
    def _update_contract_state(self):
        today = date.today()
        for order in self:
            if order.state not in ['cancel','done']:
                if order.end_date and today > order.end_date:
                    order.state = 'done'
                elif order.date and today >= order.date:
                    if not order.order_line :
                        raise ValidationError('order lines are required ')
                    order.sudo().action_confirm()
    def write(self, vals):
        res = super(Sale0rder, self).write(vals)
        if any(field in vals for field in ['date', 'end_date']):
            self._update_contract_state()
        return res
    def action_force_end_contract(self):
        today = date.today()
        for order in self:
            order.write({
                'state': 'done',
                'end_date': today
            })
    @api.model
    def _cron_update_contract_states(self):
        today = date.today()
        orders_to_activate = self.search([
            ('state', 'not in', ['cancel','sale','done']),
            ('date', '<=', today),
            '|', ('end_date', '=', False), ('end_date', '>=', today)
        ])
        if orders_to_activate:
            for order in orders_to_activate:
                if order.order_line :
                    order.sudo().action_confirm()
        orders_to_expire = self.search([
            ('state', 'not in', ['cancel', 'done']),
            ('end_date', '!=', False),
            ('end_date', '<', today)
        ])
        if orders_to_expire:
            for order in orders_to_expire:
                order.write({'state': 'done'})

