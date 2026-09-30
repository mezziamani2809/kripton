# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from xml import etree

from psycopg2 import sql, DatabaseError

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _rec_name = "name"


    user_active = fields.Boolean()
    related_user = fields.Char()
    display_name = fields.Char(compute='_compute_display_name', recursive=True, store=True, index=True)

    @api.depends('is_company', 'name', 'parent_id.display_name', 'type', 'company_name')
    def _compute_display_name(self):
        diff = dict(show_address=None, show_address_only=None, show_email=None, html_format=None, show_vat=None)
        names = dict(self.with_context(**diff).name_get())

        for partner in self:
            # Obtenir le nom complet avant la virgule
            full_name = names.get(partner.id)
            if full_name:
                # Séparer le nom complet en deux parties: avant la virgule et après
                name_parts = full_name.split(',', 1)
                print('name_parts',name_parts)
                if len(name_parts) > 1:
                    # Assigner la deuxième partie (après la virgule) comme display_name
                    partner.display_name = name_parts[1].strip()
                    print('partner.display_name ',partner.display_name )

                else:
                    # S'il n'y a pas de virgule, assigner le nom complet
                    partner.display_name = full_name.strip()
                    print('partner.display_name ',partner.display_name )
            else:
                partner.display_name = False


    def create_users(self):
        self.user_active ='True'
        self.related_user =self.name
        vals = {
            'name': self.name,
            'login':self.email,
            'email': self.email,
            'partner_id':self.id,
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id]),(4, self.env.ref('hr_timesheet.group_hr_timesheet_user').id),(4, self.env.ref('project.group_project_user').id)],
            'password': 'sapres123!'
        }
        users = self.env['res.users'].create(vals)

    company_type = fields.Selection(string='Company Type',
                                    selection=[('person', 'Freelancer'), ('company', 'Company')],
                                    compute='_compute_company_type', inverse='_write_company_type')
    final_customer_rank = fields.Integer(default=0, copy=False, string="Final customer")
    iban = fields.Char(string='IBAN')
    bic = fields.Char(string='BIC')
    type_contact = fields.Selection([
        ('externe', 'Consultant Externe'),
        ('interne', 'Consultant Interne'),
    ], string="Type")
    timesheets_attachment = fields.Many2many('ir.attachment', string="Attachment", copy=False)
    tcs_ba_id = fields.Char(string='TCS BA ID', default="")
    related_user_id = fields.Many2one('res.users', string='Related User',
                                      help='This filed contains the related user of the partner if there is any.')
    filename = fields.Char(string='Nom de document')
    file = fields.Binary(string="Contract")
    name = fields.Char(compute="get_name", inverse='reverse_name', store=True, readonly=False)
    first_name = fields.Char("First name")
    last_name = fields.Char("Last name")
    tva = fields.Char("VAT")

    _sql_constraints = [("check_name", "CHECK( 1=1 )", "Contacts require a name.")]

    @api.depends("first_name", "last_name")
    def get_name(self):
        for record in self:
            record.name = " ".join(n for n in (record.first_name, record.last_name) if n)

    @api.model_create_multi
    def create(self, vals_list):
        ctx = dict(self.env.context)
        for vals in vals_list:
            t_name = vals.get("name", ctx.get("default_name"))
            if t_name is not None:
                new_inv_name = self.get_reverse_name(self.new_modified_name(t_name))
                for key, value in new_inv_name.items():
                    if not vals.get(key):
                        vals[key] = value
                if "name" in vals:
                    del vals["name"]
                if "default_name" in ctx:
                    del ctx["default_name"]

        return super(ResPartner, self.with_context(ctx)).create(vals_list)

    @api.model
    def new_modified_name(self, name):
        if isinstance(name, bytes):
            name = name.decode("utf-8")
        try:
            name = " ".join(name.split()) if name else name
        except UnicodeDecodeError:
            name = " ".join(name.decode("utf-8").split()) if name else name
        return name

    def reverse_name(self):
        for record in self:
            record.name = record.new_modified_name(record.name)
            record.revert_name()

    @api.model
    def get_reverse_name(self, name):
        sequence = 'fl'
        portion = name.split("," if sequence == "lfc" else " ", 1)
        if len(portion) > 1:
            if sequence == "fl":
                portion = [" ".join(portion[1:]), portion[0]]
            else:
                portion = [portion[0], " ".join(portion[1:])]
        else:
            while len(portion) < 2:
                portion.append(False)
        if len(portion) == 2:
            if not portion[1]:
                res = {"last_name": portion[1], "first_name": portion[0]}
            else:
                res = {"last_name": portion[0], "first_name": portion[1]}
            return res

    def revert_name(self):
        for record in self:
            portion = record.get_reverse_name(record.name)
            record.last_name = portion["last_name"]
            record.first_name = portion["first_name"]

    @api.model
    def get_views(self, views, options=None):
        """ Super get_views function to write into related user when opening the view.

            :param views: list of [view_id, view_type]
            :param dict options: a dict optional boolean flags, set to enable:

            :return: dictionary with fields_views, fields and optionally filters

        """
        res = super().get_views(views, options)
        res_users = self.env['res.users'].search([])
        for users in res_users:
            print('users',users)
            res_partner = self.search([])
            for partner in res_partner:
                if users.partner_id.id == partner.id:
                    partner.write({
                        'related_user_id': users.id,
                    })



    @api.model_create_multi
    def create(self, vals_list):
        print('self',self)
        search_partner_mode = self.env.context.get('res_partner_search_mode')
        is_customer = search_partner_mode == 'customer'
        is_final_customer = search_partner_mode == 'final_customer'
        is_supplier = search_partner_mode == 'supplier'

        if search_partner_mode:
            for vals in vals_list:
                if is_final_customer and 'final_customer_rank' not in vals:
                    vals['final_customer_rank'] = 1
                if is_customer and 'customer_rank' not in vals:
                    vals['customer_rank'] = 1
                elif is_supplier and 'supplier_rank' not in vals:
                    vals['supplier_rank'] = 1
        return super().create(vals_list)

    def _increase_rank(self, field, n=1):
        if self.ids and field in ['customer_rank', 'supplier_rank', 'final_customer_rank']:
            try:
                with self.env.cr.savepoint(flush=False):
                    query = sql.SQL("""
                        SELECT {field} FROM res_partner WHERE ID IN %(partner_ids)s FOR UPDATE NOWAIT;
                        UPDATE res_partner SET {field} = {field} + %(n)s
                        WHERE id IN %(partner_ids)s
                    """).format(field=sql.Identifier(field))
                    self.env.cr.execute(query, {'partner_ids': tuple(self.ids), 'n': n})
                    for partner in self:
                        self.env.cache.remove(partner, partner._fields[field])
            except DatabaseError as e:
                if e.pgcode == '55P03':
                    _logger.debug('Another transaction already locked partner rows. Cannot update partner ranks.')
                else:
                    raise e

