# -*- coding:utf-8 -*-

import babel
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
from pytz import timezone
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

class HrEmployeeDocuments(models.Model):
    _name = 'hr.employee.documents.type'
    _description = 'HR Employee Documents'

    name = fields.Char(string='Documents Type')


class HrEmployeeDocuments(models.Model):
    _name = 'hr.employee.documents'
    _description = 'HR Employee Documents'

    name = fields.Char(string='Documents Name')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    type_id = fields.Many2one('hr.employee.documents.type', string='Type', required=True)
    date_from = fields.Date(string='Date From', readonly=False, required=True,
                            default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    date_to = fields.Date(string='Date To', readonly=False, required=True,
                          default=lambda self: fields.Date.to_string(
                              (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()))
    doc_attachment_id = fields.Many2many('ir.attachment',
                                         string="Document",
                                         help='You can attach the copy of your document',
                                         copy=False)

    description = fields.Text(string='Description', copy=False)
    user_id = fields.Many2one('res.users', 'Users', ondelete='cascade', related='employee_id.user_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Confirme')], string='Status', default='draft')
    def action_confirm(self):
        print('innn')
        for rec in self:
            if rec.state =='draft':
                print('innn')
                rec.state = 'done'
                mail_template = self.env.ref(
                    'Kripton_documents.doc_template')
                mail_template.send_mail(rec.id, force_send=True)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def _document_count(self):
        for each in self:
            document_ids = self.env['hr.employee.documents'].search(
                [('employee_id', '=', each.id)])
            each.document_count = len(document_ids)

    def document_view(self):
        self.ensure_one()
        domain = [
            ('employee_id', '=', self.id)]
        return {
            'name': _('Documents'),
            'domain': domain,
            'res_model': 'hr.employee.documents',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                           Click to Create for New Payroll
                        </p>'''),
            'limit': 80,
            'context': {'default_employee_id': self.id},
        }

    document_count = fields.Integer(compute='_document_count',
                                    string='# Payroll')
