# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import AccessError


class MergeInvoice(models.TransientModel):
    _name = "merge.invoice"
    _description = "Invoice Merge Wizard"

    invoice_ids = fields.Many2many('account.move',
                                   help="Selected invoices to merge",
                                   string="Invoice")
    partner_id = fields.Many2one('res.partner', string="Customer",
                                 help="The new invoice will be created"
                                      " for selected partner")
    target_invoice_id = fields.Many2one('account.move',
                                        string="Merge to existing",
                                        help="Select a invoice if you want to "
                                             "merge other invoices to selected"
                                             " one, Otherwise leave it empty")
    merge_type = fields.Selection(
        [('cancel', 'Cancel others'), ('keep', 'Keep others as it is')],
        string="Merge type", default="cancel",
        help="Select the merge type to decide what to do with other invoices")

    def action_merge_invoice(self):
        """Method for merge invoices"""
        # Checking for is there any exceptions
        if len(list(set(self.invoice_ids))) == 1:
            raise AccessError(_("Merging is not possible on single invoice"))
        if any(state in ['posted', 'cancel'] for state in
               self.invoice_ids.mapped('state')):
            raise AccessError(_("Merging is only possible on draft state "
                                "invoices"))
        if len(list(set(self.invoice_ids.mapped('move_type')))) > 1:
            raise AccessError(_("Merging is only Different type moves,"
                                " please select same type"))
        # If there is no exceptions continue with the merging
        invoices = self.invoice_ids
        invoice_lines = []
        pay_reference = []
        if self.target_invoice_id:
            target_invoice = self.target_invoice_id
            invoices -= self.target_invoice_id
            pay_reference.append(target_invoice.name if
                                 target_invoice.name != "/" else
                                 "Draft " + str(target_invoice.id))
        else:
            target_invoice = self.env['account.move'].with_context(
                check_move_validity=False).create(
                {'partner_id': self.partner_id.id,
                 'move_type': invoices[0].move_type,
                 'invoice_origin': invoices[0].invoice_origin,
                 })
        for record in invoices:
            for line in record.line_ids:

                if line.display_type not in ["payment_term", "tax"]:
                    invoice_lines += line.with_context(
                        check_move_validity=False).copy(
                        {'move_id': target_invoice.id,
                         'sale_line_ids': line.sale_line_ids})
            pay_reference.append(record.name if
                                 record.name != "/" else
                                 "Draft " + str(record.id))
            if self.merge_type == "cancel":
                record.button_cancel()

        for order in invoices.mapped('invoice_origin'):
            sale_orders = self.env['sale.order'].search([('name', '=', order)])
            for sale_order in sale_orders:
                for line in sale_order.order_line:
                    for invoice_line in target_invoice.invoice_line_ids:

                        if invoice_line.sale_line_ids and invoice_line.sale_line_ids[0].id == line.id:
                            line.write({'invoice_lines': [(4, invoice_line.id)]})
        target_invoice.write(
            {'payment_reference': f"Merged ({(', '.join(pay_reference))})"})
