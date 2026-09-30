# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, Command, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError

import logging
import base64
import zipfile
from io import BytesIO

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    end_date_timesheets = fields.Date('End Date Timesheets')
    contact_id = fields.Many2one(
        'res.partner',
        string="Contact",
        required=False,
        domain="[('parent_id', '=', partner_id)]",
    )
    ausgangsrechnungen_date = fields.Date(string="AUSGANGSRECHNUNGEN Date")


    vendor_id = fields.Many2one('res.partner', string="Consultant", required=False)
    timesheets_attachment = fields.Many2many('ir.attachment', string="Attachment", copy=False)
    to_gutschrift = fields.Boolean(string='Gutschrift', default=False)
    multi_vendor_id = fields.Many2many('res.partner', string="Multi Consultant", required=False)
    tcs = fields.Boolean(string='TCS', default=False)
    is_employee = fields.Boolean(string='Is Employee?', default=False)
    employee_id = fields.Many2one('hr.employee', string="Employees")
    status = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('sent', 'Sent'),
        ('cancel', 'Cancelled'),
    ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')
    invoice_number_bill = fields.Char(string='Invoice Number')
    service_contract = fields.Date("Service contract Date")
    gutschrift_j = fields.Boolean("Rechnung")
    gutschrifthays = fields.Boolean("Gutschrift")
    invoice_number = fields.Char(string='Number', compute='_compute_invoice_number', store=True)
    ref_number = fields.Char(string='Number', compute='_compute_ref_number', store=True)
    invoices_form = fields.Selection(selection=[
        ('invoices', 'Invoices'),
        ('rechnung', 'Rechnung'),
        ('tcs', 'TCS'),
        ('standard_rechnung', 'Standard Rechnung'),
        ('stornorechnungs', 'Stornorechnung'),
    ], string='Invoices Form')
    invoice_attachment = fields.Many2one(string="Invoice Attachment", comodel_name='ir.attachment', index=True,
                                         copy=False)
    doc_attachment_id = fields.Binary(string="Invoice Attachment")
    doc_attachment_name = fields.Char(string="Invoice Attachment")

    def action_print_new(self):
        if self.invoices_form == 'standard_rechnung':
            report = self.env.ref('standard_invoice_report.action_Standard_report_print_thermal_so')
        elif self.invoices_form == 'tcs':
            report = self.env.ref('tcs_invoice_report.action_report_print_thermal_so')
        elif self.invoices_form == 'rechnung':
            report = self.env.ref('rechnung_invoice_report.action_report_print_thermal_so')
        elif self.invoices_form == 'stornorechnungs':
            report = self.env.ref('stornorechnungs_report.action_stornorechnungs_report_print_thermal_so')
        else:
            report = self.env.ref('account.account_invoices_without_payment')

        report_action = report.report_action(self)

        return report_action

    def action_attachments_download(self):
        if not self.ids:
            raise UserError('Aucun document sélectionné à télécharger.')

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for document in self:
                if document.doc_attachment_id:
                    attachment_name = document.name or 'document'
                    zip_file.writestr(f'{attachment_name}.pdf', base64.b64decode(document.doc_attachment_id))

        zip_buffer.seek(0)
        zip_data = zip_buffer.read()
        zip_buffer.close()
        folder_name = "Invoices"
        zip_filename = f'{folder_name}.zip'

        # Créez une instance d'ir.attachment pour le fichier ZIP
        attachment = self.env['ir.attachment'].create({
            'name': zip_filename,
            'datas': base64.b64encode(zip_data),
            'res_model': 'account.move',
            'res_id': 0,
            'type': 'binary',
            'public': True,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % (attachment.id),
            'target': 'self',
        }

    @api.depends('name')
    def _compute_invoice_number(self):
        for record in self:
            if not record.gutschrifthays:
                if record.name and '-' in record.name:
                    parts = record.name.split('-')
                    record.invoice_number = parts[1][-3:] + parts[0]
                else:
                    record.invoice_number = record.name
            else:
                record.invoice_number = record.name
    @api.depends('name')
    def _compute_ref_number(self):
        for record in self:
            print('record')
            if record.move_type == 'out_refund':
                print('inn')
                if record.ref and 'Reversal of: ' in record.ref:
                    parts_ = record.ref.split('Reversal of: ')
                    if '-' in parts_[1]:
                        parts = parts_[1].split('-')
                        record.ref_number = parts[1][-3:] + parts[0]

    @api.onchange('gutschrifthays')
    def gutschrift_hays(self):
        if self.gutschrifthays:
            self.journal_id = self.env.ref('kripton_invoicing.account_journal_gutschrift').id
        else:
            self.journal_id = 10
            if self.journal_id and self.journal_id.currency_id:
                new_currency = self.journal_id.currency_id
                if new_currency != self.currency_id:
                    self.currency_id = new_currency
                    self._onchange_currency()
            if self.state == 'draft' and self._get_last_sequence(lock=False) and self.name and self.name != '/':
                self.name = '/'

    def action_post(self):
        # Call the parent class's action_post method using super.
        super(AccountMove, self).action_post()

        # Update the state to 'sent'.
        self.write({'status': 'generated'})

    invoice_send = fields.Boolean(string='Sending the invoice', default=False)

    @api.onchange('invoice_send')
    def onchange_invoice_send(self):
        if self.invoice_send:
            self.status = 'sent'
            self.is_move_sent = True

    @api.depends('invoice_line_ids', 'invoice_line_ids.end_date')
    def update_multi_vendor_id(self):
        for order in self:
            order.multi_vendor_id = [(6, 0, order.invoice_line_ids.mapped('end_date').ids)]


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    service_type = fields.Selection([
        ('mixte', 'Mixte'),
        ('site', 'On Site'),
        ('romote', 'Remote'),
    ], string="Service Type")
    vendor_id = fields.Many2one('res.partner', string='Consultant')
    tcs = fields.Boolean(string='TCS', default=False)
    tcs_ba_id = fields.Char(string='TCS BA ID', default="")
    end_date_timesheet = fields.Date('End Date Timesheets', required=False, index=True)


class AccountInvoiceSend(models.TransientModel):
    _inherit = 'account.invoice.send'

    def _send_email(self):
        # Call the parent class's _send_email method using super.
        super(AccountInvoiceSend, self)._send_email()

        # Update the state to 'sent' for the relevant invoices.
        if self.env.context.get('mark_invoice_as_sent'):
            invoices_to_mark_sent = self.mapped('invoice_ids')
            invoices_to_mark_sent.sudo().write({'status': 'sent'})

