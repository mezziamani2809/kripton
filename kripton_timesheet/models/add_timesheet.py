import base64

from odoo import api, fields, models
from odoo.cli.scaffold import template
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression

class ProjectProject(models.Model):
    _inherit = "project.project"

    multi_vendor_id = fields.Many2many('res.partner', string="Multi Consultant")

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.onchange('consultant_id')
    def consultant_id_onchange(self):
        domain = {'project_id': []}
        project_ids = []

        if self.consultant_id:
            projects = self.env['project.project'].search([('multi_vendor_id', 'in', self.consultant_id.id)])
            project_ids = projects.ids
            domain['project_id'] = [('id', 'in', project_ids)]

        return {'domain': domain}

class ConsultantSpace(models.Model):
    _name = 'consultant.space'
    _description = 'Consultant Space'
    _rec_name = "project_id"
    _order = "create_date desc"

    invoice_attachment = fields.Binary(string="Invoices Attachment")

    timesheet_attachment = fields.Binary(string="Timesheet Attachment")
    timesheet_name = fields.Char(string='Timesheets Name')
    invoice_name = fields.Char(string='Invoice Document Name')

    timesheet_ids = fields.One2many('account.analytic.line', 'consultant_space_id', string='Timesheets')
    state = fields.Selection([
        ('draft', 'Draft'),  # Use more descriptive value names
        ('checked', 'Checked'),
    ], string='Status', readonly=False, index=True, copy=False, default='draft', tracking=True)
    invoice_state = fields.Selection([
        ('not_paid', 'Not Generated'),  # Use more descriptive value names
        ('paid', 'Generated'),
    ], string='Invoice State', readonly=False, index=True, copy=False, default='not_paid', tracking=True)

    project_id = fields.Many2one('project.project', 'Project', compute='_compute_project_info', store=True)
    date = fields.Date('Date', compute='_compute_project_info', store=True)
    end_date = fields.Date('End Date', compute='_compute_project_info', store=True)
    is_employee = fields.Boolean(string="Employees", compute='_compute_info', store=True)
    is_send = fields.Boolean(string="Is Send", readonly=True)

    def action_to_send(self):
        for rec in self:
            mail_template = self.env.ref('kripton_timesheet.timesheet_mail_template')

            # Create an attachment
            if rec.timesheet_attachment:
                attachment = self.env['ir.attachment'].create({
                    'name': rec.timesheet_name,
                    'type': 'binary',
                    'datas': rec.timesheet_attachment,
                    'res_model': 'consultant.space',
                    'res_id': rec.id,
                    'mimetype': 'application/pdf',  # Adjust MIME type as needed
                })

                # Attach the file to the email
                mail_template.attachment_ids = [(6, 0, [attachment.id])]

            # Send the email
            mail_template.send_mail(rec.id, force_send=True)
            rec.is_send = True


    @api.onchange('consultant_id')
    def _onchange_consultant_id(self):
        if self.consultant_id and self.timesheet_ids:
            for line in self.timesheet_ids:
                line.consultant_id = self.consultant_id.id
    @api.onchange('timesheet_ids')
    def _onchange_consultant_id(self):
        if self.timesheet_ids:
            for line in self.timesheet_ids:
                self.consultant_id = line.consultant_id.id

    @api.depends('consultant_id')
    def _compute_info(self):
        for info in self:
            if info.consultant_id.related_user_id:
                info.is_employee = True
            else:
                info.is_employee = False

    def open_related_form(self):
        return {
            'name': 'Related Contract',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.project_id.sale_order_id.id,
            'target': 'current',
        }

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id') or self.env.user.id

    user_id = fields.Many2one(
        'res.users',
        required=True,
        default=_default_user)

    @api.depends('timesheet_ids')
    def _compute_project_info(self):
        for record in self:
            if record.timesheet_ids:
                project_id = record.timesheet_ids[0].project_id
                date = record.timesheet_ids[0].date
                end_date = record.timesheet_ids[-1].end_date
                record.project_id = project_id.id
                record.date = date
                record.end_date = end_date

    def action_to_check(self):
        for line in self.timesheet_ids:
            line.write({
                'invoice_attachment': self.invoice_attachment,
                'timesheet_attachment': self.timesheet_attachment,
                'invoice_name': self.invoice_name,
                'timesheet_name': self.timesheet_name,
            })
            last_purchase_line = self.env['purchase.order.line'].search([('sale_line_id', '=', line.so_line.id)])
            for imp in self:
                if imp.state == "draft":
                    imp.state = "checked"
                    for rec in last_purchase_line:
                        if rec.product_uom == line.so_line.product_uom:
                            rec.qty_received = line.so_line.qty_delivered
                        else:
                            if line.so_line.number_of_hour_by_day != 0:
                                rec.qty_received = line.so_line.qty_delivered / line.so_line.number_of_hour_by_day

    def action_consultant_space_delete(self):
        for record in self:
            record.timesheet_ids.unlink()
            record.unlink()

    @api.model
    def _default_user(self):
        return self.env.context.get('consultant_id') or self.env.user.partner_id.id

    consultant_id = fields.Many2one(
        'res.partner',
        string="Consultant",
        required=True,
        default=_default_user
    )

    def action_to_paid(self):
        for line in self:
            if line.invoice_state == "not_paid":
                line.invoice_state = "paid"

    def add_timesheet_all_(self):
        for rec in self.timesheet_ids:
            rec.write({
                'invoice_attachment': self.invoice_attachment,
                'timesheet_attachment': self.timesheet_attachment,
                'invoice_name': self.invoice_name,
                'timesheet_name': self.timesheet_name,
            })
        for line in self:
            if line.state == 'draft':
                line.state = "confirm"

    def action_to_paid_(self):
        for consultant_space in self:
            purchase_order = self.env['purchase.order'].search([
                ('origin', '=', consultant_space.project_id.sale_order_id.name),
            ])
            if purchase_order:
                for rec in purchase_order:
                    if consultant_space.consultant_id.parent_id.id == rec.partner_id.id:
                        purchase_order.action_create_invoice()
                        consultant_space.write({
                            'invoice_state': 'paid',
                        })
                    elif consultant_space.consultant_id == rec.partner_id:
                        purchase_order.action_create_invoice()
                        consultant_space.write({
                            'invoice_state': 'paid',
                        })
                    else:
                        pass



class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    _description = 'Analytic Line'

    consultant_space_id = fields.Many2one('consultant.space')
