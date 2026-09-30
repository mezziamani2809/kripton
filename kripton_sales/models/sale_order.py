# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, float_round
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    contract_type_po = fields.Selection([
        ('po', 'With PO'),
        ('without_po', 'Without PO'),
    ], string="Contract Type")
    invoice_amount_total = fields.Monetary(
        string="PO Balance",
        compute="_compute_invoice_amount_total",
        store=True,
        currency_field='currency_id'
    )

    @api.depends('invoice_ids.amount_untaxed_signed', 'invoice_ids.state', 'po_amount')
    def _compute_invoice_amount_total(self):
        for order in self:
            # Filtrer uniquement les factures validées (state='posted')
            invoices = order.invoice_ids.filtered(lambda inv: inv.state == 'posted')
            order.invoice_amount_total = order.po_amount - sum(invoices.mapped('amount_untaxed_signed'))

    date_po = fields.Date('Start Date PO', required=False, index=True, default=fields.Date.context_today)
    end_date_po = fields.Date('End Date PO', required=False, index=True)
    timesheets_attachment_po = fields.Binary(string="Purchase Order (PO)")
    po_amount = fields.Monetary(string='PO amount')
    po_balance = fields.Monetary(string='PO Balance')
    invoice_name = fields.Char(string='Invoice Document Name')
    vendor_id = fields.Many2one('res.partner', string="Consultant", required=False)
    multi_vendor_id = fields.Many2many('res.partner', string="Multi Consultant", required=False,
                                       compute="update_multi_vendor_id", store=True)
    final_customer_id = fields.Many2one('res.partner', string="Final Customer")
    final_customer = fields.Char(string="Final Customer")
    date = fields.Date('Start Date', required=False, index=True, default=fields.Date.context_today)
    end_date = fields.Date('End Date', required=False, index=True)
   
    @api.onchange('end_date')
    def _onchange_end_date(self):
        """Immediate UI feedback: if the contract was expired (done) and the
        end_date is extended to today or later, switch it back to In progress.
        If the end_date is set in the past, mark it as Expired."""
        today = date.today()
        for order in self:
            if order.state == 'cancel':
                continue
            if order.end_date:
                if order.end_date >= today and order.state == 'done':
                    order.state = 'sale'
                elif order.end_date < today and order.state not in ['cancel', 'done']:
                    order.state = 'done'

    @api.onchange('date', 'end_date')
    def _onchange_date(self):
        for rec in self:
            if rec.date or rec.end_date:
                for line in rec.order_line:
                    line.sudo().write({'date': rec.date, 'end_date': rec.end_date})

    quantity_by_day = fields.Float('PO Volume')
    number_of_hour_by_day = fields.Integer('PO', default=8.0)
    totol_hours = fields.Integer('PO Volume ')
    contract_type = fields.Selection([
        ('d', 'Days'),
        ('h', 'Hour'),
    ], string="PO unit")
    timesheets_attachment = fields.Many2many('ir.attachment', string="Contract", copy=False)
    description = fields.Text(string='Description', copy=False)
    Signature = fields.Selection([
        ('double', 'Double'),
        ('sapres', 'Sapres'),
        ('client', 'Client'),
    ], string="Signature")
    tcs = fields.Boolean(string='TCS', default=True)
    is_employee = fields.Boolean(string='Is Employee?', default=False)
    employee_id = fields.Many2one('hr.employee', string="Employees")
    state = fields.Selection([
        ('draft', 'Client Contract'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Activated Contract'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')

    @api.depends('order_line', 'order_line.vendor_id')
    def update_multi_vendor_id(self):
        for order in self:
            order.multi_vendor_id = [(6, 0, order.order_line.mapped('vendor_id').ids)]

    def _prepare_invoice(self, ):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        if self.tcs:
            if self.employee_id:
                invoice_vals.update({
                    'tcs': self.tcs,
                    'is_employee': self.is_employee,
                    'multi_vendor_id': self.multi_vendor_id.ids,
                    'employee_id': self.employee_id,
                    'discount_amount': self.discount_amount,

                })
            else:
                invoice_vals.update({
                    'tcs': self.tcs,
                    'is_employee': self.is_employee,
                    'multi_vendor_id': self.multi_vendor_id.ids,
                    'discount_amount': self.discount_amount,

                })

        else:
            invoice_vals.update({
                'vendor_id': self.vendor_id,
                'tcs': self.tcs,

            })

        return invoice_vals

    @api.onchange('contract_typCompanye')
    def _onchange_contract_type_hours(self):
        for rec in self:
            if rec.contract_type == 'h':
                rec.totol_hours = 0.0

    @api.onchange('contract_type')
    def _onchange_contract_type_days(self):
        for rec in self:
            if rec.contract_type == 'd':
                rec.number_of_hour_by_day = 8.0
                rec.quantity_by_day = 0.0

    @api.depends('quantity_by_day', 'number_of_hour_by_day')
    def _onchange_totol_hour(self):
        for rec in self:
            rec.totol_hours = rec.quantity_by_day * rec.number_of_hour_by_day

    @api.onchange('end_date')
    def _onchange_end_date(self):
        for rec in self:
            rec.validity_date = rec.end_date

    @api.onchange('date')
    def _onchange_end_date(self):
        for rec in self:
            rec.date_order = rec.date

    @api.constrains('date', 'end_date')
    def _check_contract_date(self):
        for event in self:
            if event.end_date and event.date:
                if event.end_date < event.date:
                    raise ValidationError(_('The closing date cannot be earlier than the beginning date.'))

    @api.onchange('order_line')
    def _onchange_number_of_hour_by_day(self):
        for rec in self:
            for line in rec.order_line:
                rec.number_of_hour_by_day = line.number_of_hour_by_day

    @api.onchange('order_line')
    def _onchange_product_uom_qty(self):
        for rec in self:
            for line in rec.order_line:
                line.product_uom_qty = 0.0

    def _get_invoiceable_lines(self, final=False):
        """Return the invoiceable lines for order `self`."""
        down_payment_line_ids = []
        invoiceable_line_ids = []
        pending_section = None
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        for line in self.order_line:
            if line.display_type == 'line_section':
                # Only invoice the section if one of its lines is invoiceable
                pending_section = line
                continue
            if line.display_type != 'line_note' and float_is_zero(line.qty_to_invoice, precision_digits=precision):
                continue
            if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final) or line.display_type == 'line_note':
                if line.is_downpayment:
                    # Keep down payment lines separately, to put them together
                    # at the end of the invoice, in a specific dedicated section.
                    down_payment_line_ids.append(line.id)
                    continue
                if pending_section:
                    invoiceable_line_ids.append(pending_section.id)
                    pending_section = None
                invoiceable_line_ids.append(line.id)

        return self.env['sale.order.line'].browse(invoiceable_line_ids + down_payment_line_ids)
