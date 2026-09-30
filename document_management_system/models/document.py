# -*- coding: utf-8 -*-

import logging
import re
import base64
import zipfile
from io import BytesIO
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

# Matches one or MORE stacked prefixes like:
#   AR_2605_4_ / ER_2605_12_ / KA_..._ / PB_..._
#   VB2605_4_ / VB_2605_4_ / KK2605_4_ / KK_2605_4_
#   and tolerates a stray "v_" in front of each stacked prefix (v_ER_2605_5_)
# The trailing "+" strips multiple stacked prefixes in one pass, so it also
# repairs already-corrupted names like
#   "ER_2605_4_ER_2605_5_Invoice.pdf"      -> "Invoice.pdf"
#   "ER_2605_4_v_ER_2605_5_Invoice.pdf"    -> "Invoice.pdf"
PREFIX_RE = re.compile(
    r'^(?:(?:v_)?(?:(?:AR|ER|KA|PB)_\d{4}_\d+_|(?:VB|KK)_?\d{4}_\d+_))+'
)


class Document(models.Model):
    _name = "document.document"
    _description = 'Document'
    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'sequence,id'
    _order = 'parent_id,sequence,id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    parent_path = fields.Char(index=True)
    parent_left = fields.Integer(index=True)
    parent_right = fields.Integer(index=True)
    active = fields.Boolean(default=True)
    old = fields.Boolean(default=False)
    sequence = fields.Integer(default=0)
    color = fields.Integer()
    name = fields.Char('Name', required=True)
    document_management = fields.One2many('sapres.document.document', 'document_ref', string="Accounting")
    full_name = fields.Char('Full Name', compute='_compute_full_name')
    description = fields.Char('Description')
    content = fields.Html('Content')
    parent_id = fields.Many2one('document.document', "Parent", ondelete="cascade", index=True)
    parent_full_name = fields.Char("Path", related='parent_id.full_name')
    child_ids = fields.One2many('document.document', 'parent_id', string='Child')
    child_count = fields.Integer(compute='_compute_child_count', string='Child Count')

    _sql_constraints = [
        ('parent_id_name_uniq', 'unique(parent_id, name)', 'Name already exists!'),
    ]

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('Parent already recursive!'))

    def _compute_child_count(self):
        relative_field = self._fields.get("child_ids")
        comodel_name = relative_field.comodel_name
        inverse_name = relative_field.inverse_name
        count_data = self.env[comodel_name].read_group([(inverse_name, 'in', self.ids)], [inverse_name], [inverse_name])
        mapped_data = dict(
            [(count_item[inverse_name][0], count_item['%s_count' % inverse_name]) for count_item in count_data])
        for record in self:
            record.child_count = mapped_data.get(record.id, 0)

    def name_get(self):
        if self.env.context.get('display_full_name', False):
            pass
        else:
            return super(Document, self).name_get()

        def get_names(record):
            res = []
            while record:
                res.append(record.name or '')
                record = record.parent_id
            return res

        return [(record.id, " / ".join(reversed(get_names(record)))) for record in self]

    def _compute_full_name(self):
        res_dict = dict(self.with_context({'display_full_name': True}).name_get())
        for record in self:
            record.full_name = res_dict.get(record.id, "")

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        default.update(name=_("%s (copy)") % (self.name or ''))
        return super(Document, self).copy(default)

    def action(self):
        self.ensure_one()
        context = self.env.context
        if self.document_count == 0:
            action_id = context.get('module_action_id')
            if action_id:
                action_dict = self.env.ref(action_id).read([
                    "type", "res_model", "view_mode", "domain"
                ])[0]
                action_dict["name"] = self.name

        else:
            action_id = 'document_management_system.action_document_main_'
            action_dict = self.env.ref(action_id).read([
                "type", "res_model", "view_mode", "domain", "context"
            ])[0]
            action_dict["name"] = self.name
            action_dict["domain"] = [('document_ref', '=', self.id)]
            action_dict["context"] = {'default_document_ref': self.id, }
        return action_dict

    def document_view_(self):
        self.ensure_one()
        domain = [
            ('document_ref', '=', self.id)]
        return {
            'name': _('Documents'),
            'domain': domain,
            'res_model': 'sapres.document.document',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form,kanban',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                           Click to Create for New Documents
                        </p>'''),
            'limit': 80,
            'context': {
                'default_document_ref': self.id,
            }}

    def _document_count(self):
        for each in self:
            document_ids = self.env['sapres.document.document'].search([('document_ref', '=', each.id)])
            each.document_count = len(document_ids)

    document_count = fields.Integer(compute='_document_count', string='# Documents')


class SapresDocumentsDocument(models.Model):
    _name = 'sapres.document.document'
    _description = 'Sapres Documents'

    # ------------------------------------------------------------------
    # Fields
    # ------------------------------------------------------------------
    row_number = fields.Integer("Numéro de ligne", readonly=True, copy=False, default=0)

    # BLOCKER : une fois le nom mis à jour, ce flag passe à True et le record
    # ne sera PLUS JAMAIS renommé par _run_name_update.
    name_updated = fields.Boolean(
        string="Nom déjà mis à jour",
        default=False,
        copy=False,
        help="Bloque toute nouvelle mise à jour du nom par _run_name_update."
    )

    document_ref = fields.Many2one('document.document', copy=False)

    name = fields.Char(string='Nom de document')
    ref = fields.Char(string='Reference', required=True, copy=False, readonly=True, index=True,
                      default=lambda self: _('New'))
    doc_attachment_id = fields.Binary(string="Attachment")
    sequence_name = fields.Char("Sequence", readonly=True)
    sequence_parent_full_name = fields.Char("Sequence", readonly=True)
    sequence_ar = fields.Char("Sequence", readonly=True)
    sequence_er = fields.Char("Sequence", readonly=True)
    sequence_ka = fields.Char("Sequence", readonly=True)
    sequence_pb = fields.Char("Sequence", readonly=True)
    sequence_vb = fields.Char("Sequence", readonly=True)
    sequence_kk = fields.Char("Sequence", readonly=True)

    # ------------------------------------------------------------------
    # Numérotation
    # ------------------------------------------------------------------
    @api.model
    def _next_row_number(self, document_ref_id):
        """Renvoie (max du groupe) + 1 pour un document_ref donné.
        Numérotation stable : ne dépend pas de la position dans une liste."""
        if not document_ref_id:
            return 0
        last = self.search(
            [('document_ref', '=', document_ref_id), ('row_number', '!=', 0)],
            order='row_number desc', limit=1,
        )
        return (last.row_number or 0) + 1

    @api.model
    def _add_row_number(self):
        """Backfill uniquement : numérote les lignes encore à 0/NULL en
        reprenant (max du groupe) + 1. Les lignes déjà numérotées ne
        changent JAMAIS -> pas de décalage, pas de collision avec les noms
        déjà figés. Ne contient AUCUN accès parent non gardé : cette
        méthode ne peut donc pas planter ni provoquer de rollback."""
        all_recs = self.search([('document_ref', '!=', False)], order='id')

        # 1) Compteur courant par groupe = max déjà présent en base
        counters = defaultdict(int)
        for rec in all_recs:
            if rec.row_number:  # truthy => déjà numéroté (0 et NULL sont falsy)
                rid = rec.document_ref.id
                counters[rid] = max(counters[rid], rec.row_number)

        # 2) Attribuer aux lignes non numérotées, dans l'ordre de création
        for rec in all_recs:
            if not rec.row_number:  # 0 OU NULL
                rid = rec.document_ref.id
                counters[rid] += 1
                rec.row_number = counters[rid]
        return True

    # ------------------------------------------------------------------
    # Renommage
    # ------------------------------------------------------------------
    @api.model
    def _run_name_update(self):
        # Étape 1 : garantir que chaque ligne a un numéro (backfill sûr)
        self._add_row_number()

        # Étape 2 : ne traiter QUE les records pas encore figés.
        # Chaque record est isolé dans un savepoint : si l'un plante
        # (ex. chaîne parente incomplète), seul CE record est annulé,
        # les autres — et surtout les numéros de ligne — sont conservés.
        document_list = self.search([('name_updated', '=', False)])
        for rec in document_list:
            if not rec.name:
                continue
            try:
                with self.env.cr.savepoint():
                    self._rename_one(rec)
            except Exception as e:
                _logger.warning(
                    "Renommage ignoré id=%s (%s): %s", rec.id, rec.name, e
                )
                continue
        return True

    def _rename_one(self, rec):
        """Renomme un seul record. Toute erreur est capturée par le
        savepoint de l'appelant. Fige le record via name_updated dès qu'un
        nom a effectivement été appliqué."""
        self.ensure_one()
        dref = rec.document_ref
        if not dref:
            return

        parent_name = ''
        parent_month = ''
        document_name = ''
        if dref.parent_id and dref.parent_id.parent_id and dref.parent_id.parent_id.name:
            parent_name = dref.parent_id.parent_id.name[-2:]
            parent_month = dref.parent_id.name[:2]
            document_name = dref.parent_full_name or ''

        renamed = False

        # -------------------------------------------------- exercice 2024
        if '2024' in document_name:
            default_name = rec.name
            if dref.name == 'AUSGANGSRECHNUNGEN' and rec.sequence_ar and rec.sequence_ar not in rec.name:
                rec.name = f"AR_{parent_name}{parent_month}_{rec.sequence_ar}_{default_name}"
                renamed = True
            elif dref.name == 'EINGANGSRECHNUNGEN' and rec.sequence_er and rec.sequence_er not in rec.name:
                rec.name = f"ER_{parent_name}{parent_month}_{rec.sequence_er}_{default_name}"
                renamed = True
            elif dref.name == 'KASSE' and rec.sequence_ka and rec.sequence_ka not in rec.name:
                rec.name = f"KA_{parent_name}{parent_month}_{rec.sequence_ka}_{default_name}"
                renamed = True
            elif dref.name == 'POSTBANK' and rec.sequence_pb and rec.sequence_pb not in rec.name:
                rec.name = f"PB_{parent_name}{parent_month}_{rec.sequence_pb}_{default_name}"
                renamed = True

            if rec.sequence_vb and rec.sequence_vb not in rec.name \
                    and dref.name == 'KONTO' and dref.parent_id.name == 'VOLKSBANK':
                gp, gm = dref.parent_id.parent_id.parent_id, dref.parent_id.parent_id
                if gp and gp.name and gm and gm.name:
                    rec.name = f"VB_{gp.name[-2:]}{gm.name[:2]}_{rec.sequence_vb}_{rec.name}"
                    renamed = True

            if rec.sequence_kk and rec.sequence_kk not in rec.name \
                    and dref.name == 'KREDITKARTE' and dref.parent_id.name == 'VOLKSBANK':
                gp, gm = dref.parent_id.parent_id.parent_id, dref.parent_id.parent_id
                if gp and gp.name and gm and gm.name:
                    rec.name = f"KK_{gp.name[-2:]}{gm.name[:2]}_{rec.sequence_kk}_{rec.name}"
                    renamed = True

        # ---------------------------------------------- autres exercices
        else:
            # On retire d'abord TOUT préfixe existant (même empilé) puis on
            # reconstruit à partir du nom de base propre. Répare aussi les
            # noms corrompus type "ER_2605_4_ER_2605_5_Invoice.pdf".
            base_name = PREFIX_RE.sub('', rec.name)

            if dref.name == 'AUSGANGSRECHNUNGEN' and rec.row_number:
                rec.name = f"AR_{parent_name}{parent_month}_{rec.row_number}_{base_name}"
                renamed = True
            elif dref.name == 'EINGANGSRECHNUNGEN' and rec.row_number:
                rec.name = f"ER_{parent_name}{parent_month}_{rec.row_number}_{base_name}"
                renamed = True
            elif dref.name == 'KASSE' and rec.row_number:
                rec.name = f"KA_{parent_name}{parent_month}_{rec.row_number}_{base_name}"
                renamed = True
            elif dref.name == 'POSTBANK' and rec.row_number:
                rec.name = f"PB_{parent_name}{parent_month}_{rec.row_number}_{base_name}"
                renamed = True

            if rec.row_number and dref.name == 'KONTO' and dref.parent_id.name == 'VOLKSBANK':
                gp, gm = dref.parent_id.parent_id.parent_id, dref.parent_id.parent_id
                if gp and gp.name and gm and gm.name:
                    base_name = PREFIX_RE.sub('', rec.name)
                    rec.name = f"VB{gp.name[-2:]}{gm.name[:2]}_{rec.row_number}_{base_name}"
                    renamed = True

            if rec.row_number and dref.name == 'KREDITKARTE' and dref.parent_id.name == 'VOLKSBANK':
                gp, gm = dref.parent_id.parent_id.parent_id, dref.parent_id.parent_id
                if gp and gp.name and gm and gm.name:
                    base_name = PREFIX_RE.sub('', rec.name)
                    rec.name = f"KK{gp.name[-2:]}{gm.name[:2]}_{rec.row_number}_{base_name}"
                    renamed = True

        # BLOCKER : on fige le record dès qu'il a été renommé.
        if renamed:
            rec.name_updated = True

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------
    @api.model
    def create(self, vals):
        document_ref = self.env['document.document'].browse(vals.get('document_ref'))
        # Vérification de la validité de document_ref
        if not document_ref:
            raise UserError(_('Veuillez sélectionner un document parent valide.'))
        document_count = document_ref.document_count + 1

        # --- Numéro de ligne attribué DÈS la création (indépendant du cron).
        #     Ainsi la ligne n'affiche jamais 0, même si le cron de renommage
        #     plante ensuite sur un autre record.
        if not vals.get('row_number'):
            vals['row_number'] = self._next_row_number(vals.get('document_ref'))

        # Calcul de la valeur initiale pour chaque séquence
        document_name = document_ref.parent_full_name
        if '2024' in document_name:
            if vals.get('sequence_name', _('New')) == _('New'):
                vals['sequence_name'] = self.env['ir.sequence'].next_by_code('sapres.document.document.sequence') or _(
                    'New')
            document_test = self.env['document.document'].browse(vals.get('document_ref'))
            if vals.get('sequence_ar', _('New')) == _('New') and vals.get(
                    'document_ref') and document_test.name == 'AUSGANGSRECHNUNGEN':
                vals['sequence_ar'] = self.env['ir.sequence'].next_by_code('sapres.document.document') or _('New')

            if vals.get('sequence_er', _('New')) == _('New') and vals.get(
                    'document_ref') and document_test.name == 'EINGANGSRECHNUNGEN':
                vals['sequence_er'] = self.env['ir.sequence'].next_by_code('sapres.document.document.er') or _('New')

            if vals.get('sequence_ka', _('New')) == _('New') and vals.get(
                    'document_ref') and document_test.name == 'KASSE':
                vals['sequence_ka'] = self.env['ir.sequence'].next_by_code('sapres.document.document.ka') or _('New')

            if vals.get('sequence_pb', _('New')) == _('New') and vals.get(
                    'document_ref') and document_test.name == 'POSTBANK':
                vals['sequence_pb'] = self.env['ir.sequence'].next_by_code('sapres.document.document.pb') or _('New')

            if vals.get('sequence_vb', _('New')) == _('New') and vals.get(
                    'document_ref') and document_test.name == 'KONTO' and document_test.parent_id.name == 'VOLKSBANK':
                vals['sequence_vb'] = self.env['ir.sequence'].next_by_code('sapres.document.document.vb') or _('New')

            if vals.get('sequence_kk', _('New')) == _('New') and vals.get(
                    'document_ref') and document_test.name == 'KREDITKARTE' and document_test.parent_id.name == 'VOLKSBANK':
                vals['sequence_kk'] = self.env['ir.sequence'].next_by_code('sapres.document.document.kk') or _('New')
        else:
            vals['sequence_parent_full_name'] = str(document_count)

        res = super(SapresDocumentsDocument, self).create(vals)
        return res

    # ------------------------------------------------------------------
    # Téléchargement ZIP
    # ------------------------------------------------------------------
    def action_attachments_download(self):
        if not self.ids:
            raise UserError('Aucun document sélectionné à télécharger.')

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for document in self:
                if document.doc_attachment_id:
                    attachment_name = document.name or 'document'
                    zip_file.writestr(f'{attachment_name}.pdf', base64.b64decode(document.doc_attachment_id))

        zip_buffer.seek(0)
        zip_data = zip_buffer.read()
        zip_buffer.close()

        dref = self.document_ref

        # Accès parents gardés pour éviter un plantage None[-2:] si la
        # hiérarchie du dossier est incomplète.
        def _safe(node, attr_slice):
            return node.name[attr_slice] if node and node.name else ''

        parent_name = _safe(dref.parent_id.parent_id, slice(-2, None)) if dref.parent_id else ''
        parent_month = _safe(dref.parent_id, slice(0, 2))

        if dref.name == 'KONTOAUSZÜGE':
            folder_name = f"SapresTechno_{parent_name}{parent_month}_KONTOAUSZÜGE"
        elif dref.name == 'AUSGANGSRECHNUNGEN':
            folder_name = f"SapresTechno_{parent_name}{parent_month}_AR"
        elif dref.name == 'EINGANGSRECHNUNGEN':
            folder_name = f"SapresTechno_{parent_name}{parent_month}_ER"
        elif dref.name == 'KASSE':
            folder_name = f"SapresTechno_{parent_name}{parent_month}_KA"
        elif dref.name == 'POSTBANK':
            folder_name = f"SapresTechno_{parent_name}{parent_month}_PB"
        elif dref.name == 'KONTO':
            gp = dref.parent_id.parent_id.parent_id if dref.parent_id and dref.parent_id.parent_id else None
            gm = dref.parent_id.parent_id if dref.parent_id else None
            parent_name = _safe(gp, slice(-2, None))
            parent_month = _safe(gm, slice(0, 2))
            folder_name = f"SapresTechno_{parent_name}{parent_month}_VB"
        elif dref.name == 'KREDITKARTE':
            gp = dref.parent_id.parent_id.parent_id if dref.parent_id and dref.parent_id.parent_id else None
            gm = dref.parent_id.parent_id if dref.parent_id else None
            parent_name = _safe(gp, slice(-2, None))
            parent_month = _safe(gm, slice(0, 2))
            folder_name = f"SapresTechno_{parent_name}{parent_month}_kk"
        else:
            folder_name = "SapresTechno"
        zip_filename = f'{folder_name}.zip'

        # Créez une instance d'ir.attachment pour le fichier ZIP
        attachment = self.env['ir.attachment'].create({
            'name': zip_filename,
            'datas': base64.b64encode(zip_data),
            'res_model': 'sapres.document.document',
            'res_id': 0,  # Attachments without specific record
            'type': 'binary',
            'public': True,
        })

        # Renvoie l'URL de téléchargement en utilisant l'ID de l'ir.attachment
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % (attachment.id),
            'target': 'self',
        }
