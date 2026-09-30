import base64

from odoo import api, fields, models
from odoo.cli.scaffold import template
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression

class ProjectProject(models.Model):
    _inherit = "project.project"

