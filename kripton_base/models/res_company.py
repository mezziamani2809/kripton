# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from psycopg2 import sql, DatabaseError

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class Company(models.Model):
    _inherit = 'res.company'

    bank = fields.Char('Bank', default="Postbank")
    iban = fields.Char('IBAN', default="DE57 4401 0046 0459 9174 68")
    bic = fields.Char('BIC', default="PBNKDEFF")
    fax = fields.Char('Fax')


