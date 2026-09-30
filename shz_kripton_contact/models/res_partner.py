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

    parent_consultants_id = fields.Many2one('res.partner', string='Related partner consultants', index=True)
    parent_contacts_id = fields.Many2one('res.partner', string='Related partner contacts', index=True)

    consultants_child_ids = fields.One2many('res.partner', 'parent_consultants_id', string='Consultants', domain=[
        ('active', '=', True)])  # force "active_test" domain to bypass _search() override
    contacts_child_ids = fields.One2many('res.partner', 'parent_contacts_id', string='Contacts', domain=[
        ('active', '=', True)])  # force "active_test" domain to bypass _search() override

    def action_sync_custom_children(self):
        """
        Logique de répartition des child_ids vers les nouveaux champs
        """
        for record in self:
            if record.is_company and len(record.child_ids) > 0:
                # Filtrage selon vos conditions
                # Contacts : Client + Société
                contacts = record.child_ids.filtered(
                    lambda r: r.customer_rank > 0
                )

                # Consultants : Fournisseur + Particulier
                consultants = record.child_ids.filtered(
                    lambda r: r.supplier_rank > 0
                )

                vals = {}
                if len(contacts) > 0:
                    vals['contacts_child_ids'] = [(6, 0, contacts.ids)]
                if len(consultants) > 0:
                    vals['consultants_child_ids'] = [(6, 0, consultants.ids)]

                if vals:
                    record.write(vals)
