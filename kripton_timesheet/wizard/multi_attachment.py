import base64

from odoo import api, fields, models
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression


class AccountAnalyticLineWizard(models.Model):
    _name = 'account.analytic.line.wizard'
    _description = 'Account Analytic Line Wizard'

    invoice_attachment = fields.Binary(string="Invoices Attachment")
    timesheet_attachment = fields.Binary(string="Timesheet Attachment")
    invoice_name = fields.Char(string='Invoice Document Name')
    timesheet_name = fields.Char(string='Timesheets Name')
    timesheet_ids = fields.Many2many('account.analytic.line', string='Timesheets')

    @api.model
    def _default_user(self):
        return self.env.context.get('consultant_id') or self.env.user.partner_id.id

    consultant_id = fields.Many2one(
        'res.partner',
        string="Consultant",
        required=True,
        default=_default_user
    )

    def add_attachment_all_(self):
        for rec in self.timesheet_ids:
            rec.write({
                'line_id':rec.id,
                'invoice_attachment': self.invoice_attachment,
                'timesheet_attachment': self.timesheet_attachment,
                'invoice_name': self.invoice_name,
                'timesheet_name': self.timesheet_name,
            })
            rec._onchange_invoice_attachment()


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    _description = 'Analytic Line'

    line_id = fields.Many2one('account.analytic.line.wizard')

    def _onchange_invoice_attachment(self):
        # Define any actions you want to perform when invoice attachments are added.
        # For example, you can update invoice state or perform other operations here.
        self.ensure_one()
        if self.invoice_attachment:
            self.invoice_state = "not_paid"
            self.state = "to_check"