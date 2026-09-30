# Odoo Module: Your Module Name
# Description: This module extends the functionality of account.analytic.line and project.task models.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    _description = 'Analytic Line'

    date = fields.Date('Month', required=True, index=True, date_format='%m/%Y')
    end_date = fields.Date('End Date', required=True, index=True, default=fields.Date.context_today)
    unit_amount_on_site = fields.Float('Hours Spent on Site', default=0.0)
    unit_amount_on_remote = fields.Float('Hours Spent on Remote', default=0.0)
    timesheets_attachment = fields.Many2many('ir.attachment', string='Attachments')
    invoice_attachment = fields.Binary(string="Invoices Attachment")
    timesheet_attachment = fields.Binary(string=" Timesheet Attachment")
    invoice_name = fields.Char(string='Invoice Document Name')
    timesheet_name = fields.Char(string='Timesheets Name')
    value_name = fields.Char(string='Value Name')  # Provide a more descriptive field name
    state = fields.Selection([
        ('to_check', 'To Check'),  # Use more descriptive value names
        ('checked', 'Checked'),
    ], string='Status', readonly=False, index=True, copy=False, default='to_check', tracking=True)

    invoice_state = fields.Selection([
        ('not_paid', 'Not Paid'),  # Use more descriptive value names
        ('paid', 'Paid'),
    ], string='Invoice State', readonly=False, index=True, copy=False, default='not_paid', tracking=True)
    check_duplicate = fields.Boolean(string="Check Duplicate", compute='_compute_check_duplicate', store=True)
    service_type = fields.Char(compute='_compute_tasks_services_type', store=True, default=False)

    @api.depends('date', 'end_date', 'project_id', 'consultant_id')
    def _compute_check_duplicate(self):
        for line in self:
            domain = [
                ('date', '=', line.date),
                ('end_date', '=', line.end_date),
                ('project_id', '=', line.project_id.id),
                ('consultant_id', '=', line.consultant_id.id),
            ]
            duplicate_lines = self.search(domain)

            if duplicate_lines:
                # Set check_duplicate for the first found duplicate line to True
                line.check_duplicate = True
            else:
                line.check_duplicate = False

    def action_to_paid(self):
        for line in self:
            if line.invoice_state == "not_paid":
                line.invoice_state = "paid"

    def action_to_check(self):
        for line in self:
            last_purchase_line = self.env['purchase.order.line'].search([('sale_line_id', '=', line.so_line.id)])
            if line.state == "to_check":
                line.state = "checked"
                for rec in last_purchase_line:
                    if rec.product_uom == line.so_line.product_uom:
                        rec.qty_received = line.so_line.qty_delivered
                    else:
                        if line.so_line.number_of_hour_by_day != 0:
                            rec.qty_received = line.so_line.qty_delivered / line.so_line.number_of_hour_by_day

    @api.model
    def _default_user(self):
        return self.env.context.get('consultant_id', self.env.user.partner_id.id)

    consultant_id = fields.Many2one(
        'res.partner',
        string="Consultant",
        required=True, default=_default_user)
    is_employee = fields.Boolean(string='Is Employee?', default=False)

    @api.constrains('date', 'end_date')
    def _check_contract_date(self):
        for event in self:
            if event.end_date < event.date:
                raise ValidationError(_('The closing date cannot be earlier than the beginning date.'))

    @api.depends('task_id.name')
    def _compute_tasks_services_type(self):
        for rec in self:
            if rec.task_id:
                if rec.task_id.name:
                    if 'On Site' in rec.task_id.name:
                        rec.service_type = 'site'
                    elif 'Remote' in rec.task_id.name:
                        rec.service_type = 'remote'
                else:
                    rec.service_type = False
