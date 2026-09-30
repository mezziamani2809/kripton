# -*- coding: utf-8 -*-

from datetime import timedelta
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_send_mail_client_contract(self):
        values = self.env['res.config.settings'].default_get(
            list(self.env['res.config.settings'].fields_get()))
        if values['reminder_client_contract'] is not False:
            for record in self.search([]):
                print('record',record)
                if record.order_line:
                    for rec in record.order_line:
                        if record.state == 'sale' and rec.end_date == timedelta(int(values['set_date_client_contract_month'])) + fields.Date.today():
                            mail_template = self.env.ref(
                                'sale_invoice_due_date_reminder.client_contract_due_mail_template')
                            mail_template.send_mail(record.id, force_send=True)
                        if record.state == 'sale' and rec.end_date_po == timedelta(int(values['set_date_client_contract_month'])) + fields.Date.today():
                            mail_template = self.env.ref(
                                'sale_invoice_due_date_reminder.client_contract_due_mail_template')
                            mail_template.send_mail(record.id, force_send=True)

