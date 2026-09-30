# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.model
    def _default_po_required(self):
        active_ids = self._context.get('active_ids', [])
        if self._context.get('active_model') == 'sale.order' and active_ids:
            sale_orders = self.env['sale.order'].browse(active_ids)
            return any(order.contract_type_po == 'po' for order in sale_orders)
        return False

    po_id = fields.Many2one('sale.po', string="PO")
    po_required = fields.Boolean(default=lambda self: self._default_po_required())

    def create_invoices(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        existing_invoices = sale_orders.mapped('invoice_ids')

        res = super(SaleAdvancePaymentInv, self).create_invoices()

        if self.po_id:
            new_invoices = sale_orders.mapped('invoice_ids') - existing_invoices
            for invoice in new_invoices:
                invoice.po_id = self.po_id.id
                invoice.ref = self.po_id.client_order_ref
                invoice.invoice_payment_term_id = self.po_id.invoice_payment_term_id.id

        return res
