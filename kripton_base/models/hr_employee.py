# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from psycopg2 import sql, DatabaseError

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class EmployeeSkill(models.Model):
    _inherit = 'hr.resume.line'

    project = fields.Text(string="Project")
    company = fields.Char(string='Company')


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    vendor_id = fields.Many2one('res.partner', string="Vendor", required=False)
    freelance = fields.Boolean('Is Freelancer')
    employee = fields.Boolean('Is Employee')
    tcs = fields.Boolean(string='TCS', default=False)
    tcs_ba_id = fields.Char(string='TCS BA ID', default="")
    pc = fields.Selection([('y', 'Yes'), ('n', 'Non')], string='Laptop', default="n")
    pcid = fields.Char(string=' ID', default="")
    delivery_date = fields.Date('Delivery Date')
    description = fields.Text(string="Equipment list")
    filename = fields.Char(string='Nom de document')
    file = fields.Binary(string="Contract")
    cv_attachment = fields.Many2many('ir.attachment', string="Curriculum vitae", copy=False)
    personal_phone = fields.Char('Personal Mobile')
    personal_email = fields.Char('Personal  Email')
    street = fields.Char()
    street2 = fields.Char()
    work_email_p = fields.Char(required=True)
    zip = fields.Char(change_default=True)
    city = fields.Char(string="State")
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    filename_pass = fields.Char(string='Passport')
    type = fields.Char(string='Type')
    first_name = fields.Char(string='Type')
    has_work_permit_ = fields.Binary(string="Passport", groups="hr.group_hr_user", tracking=True)
    full_name = fields.Char(compute="full_name_", store=True, readonly=True)

    @api.onchange('tcs_ba_id')
    def _onchange_consultant_id(self):
        if self.tcs_ba_id:
                self.user_partner_id.tcs_ba_id = self.tcs_ba_id
    @api.depends("first_name", "name")
    def full_name_(self):
        for record in self:
            record.full_name = " ".join(n for n in (record.first_name, record.name) if n)

    @api.model
    def create(self, vals):
        employee = super(HrEmployee, self).create(vals)
        user = self.env['res.users'].create({
            'name': vals.get('name',False),
            'login': vals.get('work_email_p', False),
            'partner_id': employee.address_home_id.id,
            'employee_ids': [(4, employee.id, False)],
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id]),
                          (4, self.env.ref('hr_timesheet.group_hr_timesheet_user').id),
                          (4, self.env.ref('project.group_project_user').id)],
            'password': 'sapres123!',
            'hide_menu_ids': [(4, self.env.ref('kripton_timesheet.menu_consultantspace_my_invoices').id)]

        })

        # Associer l'utilisateur créé à l'employé
        employee.user_id = user.id
        employee.user_id.partner_id.related_user_id = user.id
        return employee


class EmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    vendor_id = fields.Many2one('res.partner', string="Vendor", required=False, readonly=True)
    freelance = fields.Boolean('Is Freelancer', readonly=True)
    employee = fields.Boolean('Is Employee', readonly=True)
    tcs = fields.Boolean(string='TCS', default=False, readonly=True)
    tcs_ba_id = fields.Char(string='TCS BA ID', default="", readonly=True)
    pc = fields.Selection([('y', 'Yes'), ('n', 'Non')], string='Laptop', default="n", readonly=True)
    pcid = fields.Char(string=' ID', default="")
    delivery_date = fields.Date('Delivery Date', readonly=True)
    description = fields.Text(string="Equipment list", readonly=True)
    cv_attachment = fields.Many2many('ir.attachment', string="Curriculum vitae", copy=False, readonly=True)
    filename = fields.Char(string='Nom de document')
