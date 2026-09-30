# -*- coding:utf-8 -*-

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _


class HrEmployeePayroll(models.Model):
    _name = 'hr.employee.payroll'
    _description = 'HR Employee Payroll'

    name = fields.Char(string='Payroll Name', required=False)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    date_from = fields.Date(string='Date From', required=True,
                            default=lambda self: fields.Date.today().replace(day=1))
    date_to = fields.Date(string='Date To', required=True,
                          default=lambda self: (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date())
    description = fields.Text(string='Description', copy=False)
    user_id = fields.Many2one('res.users', 'User', ondelete='cascade', related='employee_id.user_id', readonly=True)
    doc_id = fields.Binary(string="Payroll Document")
    doc_id_name = fields.Char(string="Nom de fichier")


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def _compute_payroll_count(self):
        for employee in self:
            payroll_ids = self.env['hr.employee.payroll'].search(
                [('employee_id', '=', employee.id)])
            employee.payroll_count = len(payroll_ids)

    def payroll_view(self):
        self.ensure_one()
        domain = [('employee_id', '=', self.id)]
        return {
            'name': _('Payroll'),
            'domain': domain,
            'res_model': 'hr.employee.payroll',
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

    payroll_count = fields.Integer(string='# Payroll', compute='_compute_payroll_count')
