# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval, datetime
from odoo.tools.sql import column_exists, create_column
from odoo.tools.misc import get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, float_round
from odoo.exceptions import UserError
from datetime import date

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    multi_vendor_id = fields.Many2many('res.partner', string="Multi Consultant", required=False,
                                       compute="update_multi_vendor_id", store=True)
    contract_no = fields.Char(string='Contract No.', default=lambda self: self._default_contract_no())
    man_days = fields.Char(string='Man - days.')
    fees_invoicing = fields.Html(
        string='Fees / Invoicing',
        default="""<p>The services of the Consultants are remunerated at a man-day rate of
                        <strong>
                            <span t-field="o.day_rate_site"/>
                            - €
                        </strong>

                        for onsite services</p> 
        <p>and
                        <strong>
                            <span t-field="o.day_rate_site"/>
                            -
                           €

                        </strong>
                        for remote service.</p>
        <p>The Consultant will bill the fee with value-added tax once a month.</p>
         <p> Please forward all invoices to:
                        <strong>accounting@sapres.de</strong></p>"""
    )
    @api.model
    def _default_contract_no(self):
        today = fields.Date.context_today(self)
        if isinstance(today, date):
            date_str = today.strftime('%Y-%m-%d')
        else:
            date_str = str(today)
        return f'SERVICE_{date_str}'
    whereas = fields.Html(
        string='Whereas',
        default="""<ul>
                        <li>Sapres Technologies is a company providing IT-services based upon intermediation.</li>
                        <li>The Contractor is a company or a freelance specialised in certain services, such as Software
                            development and IT consulting in the field of SAP
                        </li>
                        <li>In view of the Contractor&apos;s specific skills and expertise SAPRES TECHNOLOGIES intends to
                            outsource certain parts of its services to the Contractor.
                        </li>
                    </ul>"""
    )
    subject_matter = fields.Html(
        string='Subject Matter',
        default="""<p>(1) The Contractor shall carry out his contractual duties for SAPRES TECHNOLOGIES in information technology projects which are executed by SAPRES TECHNOLOGIES for its customers (hereinafter: SAPRES TECHNOLOGIES Customer) on the basis of the following terms and conditions.</p>
                       <p>(2) Any services shall be carried out individually and separately on the basis of individual services agreements (hereinafter &quot;Description of Services&quot; or &quot;DOS&quot;).
    Each DOS shall constitute a separate agreement, however, incorporating the terms and conditions of this Agreement.
    </p>
                        <p>(3) The contractual duties of the Contractor may consist of specific services. The nature of his duties shall be determined by the terms and conditions contained in the respective DOS.
                        </p>
                        <p>(4) In the event that any term(s) and condition(s) in the Master Agreement conflict with those of the DOS, the latter shall be given preference. 
                        </p>"""
    )
    statement_of_services = fields.Html(
        string='Statement of Services',
        default="""<p>(1) The respective DOS shall stipulate the specific contractual duties of the Contractor, including, but not limited to, details on fee/remuneration, disbursements, deadlines, due dates/duration, material and place of performance. The respective DOS shall refer to and incorporate the terms and conditions of this Agreement. Any general terms and conditions of the Contractor shall not form part of this Agreement or of any DOS under this Agreement, even if SAPRES TECHNOLOGIES does not expressly object to the inclusion of such general terms and conditions.</p>
                            <p>(2) In as far as SAPRES TECHNOLOGIES is itself a contractor of the customer, the Contractor is - in addition to observing the terms and conditions of this Agreement and of the DOS - obliged to observe such customer contract provisions to be attached as annex to the respective DOS. </p>
                            <p>(3) Any Agreement including DOS entered into between SAPRES TECHNOLOGIES and the Contractor, in which SAPRES TECHNOLOGIES assigns specific duties to its customer is conditional upon the relevant contract between SAPRES TECHNOLOGIES and the SAPRES TECHNOLOGIES Customer coming into effect and being executed.</p>
                            """
    )
    services_provision = fields.Html(
        string='General Principles of Service Provision',
        default="""<p>(1) The Parties shall agree on the specific duties of the Contractor to be set out in the respective DOS.</p>
                       <p>(2) The Contractor is independent in the execution of his services. He shall, however, observe all guidelines given by SAPRES TECHNOLOGIES, in particular observe standards and norms which are common in this sector of industry, including industry and IT standards. Unless otherwise agreed, all duties are to be carried out diligently in compliance with the actual state of the art and the principle of cost efficiency. Services provided by the Contractor shall comply with all standards and norms commonly applied at the date of DOS coming into force. The Contractor shall endeavour to obtain the best possible results, upon full use of his experience and knowledge. </p>
                       <p>(3) If services are to be provided in premises of a SAPRES TECHNOLOGIES Customer the Contractor shall comply with SAPRES TECHNOLOGIES Customer&apos;s regulations and all relevant safety and accident prevention regulations.</p>
                       <p>(4) SAPRES TECHNOLOGIES shall be entitled to set up minutes of meetings determining details of the Contractor&apos;s duties. Such minutes shall be binding upon both Parties unless the Contractor raises any objection within two weeks from service of such details.</p>
                       <p>(5) SAPRES TECHNOLOGIES assigns a project manager (SAPRES TECHNOLOGIES Project Manager) to whom the Contractor shall report any issue in connection with the Subject Matter of this Agreement or of the DOS. The Contractor shall contact the SAPRES TECHNOLOGIES Project Manager in any matter required for the execution of his duties.</p>
                       <p>(6) The use of any subcontractor for the execution of the Contractor&apos;s contractual duties requires prior written consent by SAPRES TECHNOLOGIES.</p>
                    """
    )

    compensation = fields.Html(
        string="Compensation",
        default="""<p>(1) All services are charged on the basis of time spent and material used or consumed. Invoicing to SAPRES TECHNOLOGIES will be based on SAPRES TECHNOLOGIES Customer-approved time-/activity-sheets in a SAPRES TECHNOLOGIES and-/or SAPRES TECHNOLOGIES Customer defined format, containing detailed information on any employee, time and duration of services, location of services as well as the nature of any activities. The time-/activity-sheets will be valid only if signed and dated by the SAPRES TECHNOLOGIES customer.</p>
                <p>(2) All cost estimates and pricing are considered to be provisional and non-binding. All estimates are based upon an assessment to the Contractor&apos;s best knowledge and belief including his professional experience. If, during the execution of his duties, the Contractor realises that his estimates and/or pricing are likely to be exceeded, he shall immediately inform SAPRES TECHNOLOGIES in writing.</p>
                <p>(3) Contractor&apos;s fee/remuneration does not fall due, as long as and to the extent that the SAPRES TECHNOLOGIES Customer has not accepted and paid for the services carried out by the Contractor as a result of alleged non-compliance with or violation of his contractual duties. </p>
                <p>(4) SAPRES TECHNOLOGIES is entitled to retain part or all fee/remuneration of the Contractor unless and until the Contractor provides to SAPRES TECHNOLOGIES a duly signed and dated original copy of the respective DOS</p>
                <p>(5) Disbursements expenses will be refunded only if these are expressly stipulated in the DOS and reasonably and necessarily incurred for the execution of the DOS.</p>
                <p>(6) Payments to contractor are due within 30 days from service of any invoice, however not before the time-/activity-sheets have been approved by the SAPRES TECHNOLOGIES Customer and received by SAPRES TECHNOLOGIES.</p>
                <p>(7) The Parties are aware that the agreed fee/remuneration also includes a premium to cover the risk of any SAPRES TECHNOLOGIES Customer&apos;s insolvency. With regards to the foregoing, the Parties agree that SAPRES TECHNOLOGIES has no obligation to compensate the Contractor for his services if fees / remuneration cannot be obtained from SAPRES TECHNOLOGIES&apos;s Customer due to insolvency or inability to pay. If only partial fee/remuneration can be obtained from SAPRES TECHNOLOGIES&apos;s Customer, SAPRES TECHNOLOGIES&apos;s obligation to pay Contractor is pro rata only.</p>
                <p>(8) All prices are subject to statutory VAT at any relevant time.</p>
                """
    )

    rights_intellectual_property = fields.Html(
        string="Rights / Intellectual Property",
        default="""<p>(1) The Contractor hereby assigns to SAPRES TECHNOLOGIES all rights in connection with or resulting from the duties fulfilled by the Contractor in the execution of the DOS. The Contractor shall provide all declarations and sign all documents which are required or appropriate for the assignment of the above described rights. If an assignment is not reasonably permitted in law, the Contractor shall in so far grant to SAPRES TECHNOLOGIES an exclusive, world-wide, transferable and unrestricted right to the use of such results. This includes, but is not limited to, the granting of an exclusive, world-wide, transferable unrestricted right to use all copyright protected results. This right of use includes, but is not limited to, the right to copy, change, process, translate and sell the respective results, also by means of leasing or rent, and to transfer these rights of use to any third party. The assignment and/or granting of such rights shall come into force directly upon the accomplishment of any such result. SAPRES TECHNOLOGIES hereby accepts any such assignment and the granting of such rights to use the result.</p>
                <p>(2) The Contractor expressly waives all such copy rights including the right to be named as author of such results. </p>
                <p>(3) Upon completion of the contractual duties set out in any relevant DOS or -as the case may be- upon termination of a DOS or this MAC, the Contractor shall provide to SAPRES TECHNOLOGIES all material or immaterial information, whether electronically stored or by way of any other media, which necessary for the use of the rights granted subclause 1 here above. </p>
                <p>(4) The Contractor guarantees that any result obtained in the execution of any DOS do not violate any vested titles or interests of third parties, including, but not limited to, copyrights or patents of third parties.</p>
                <p>(5) The Contractor shall, at his own costs, indemnify and hold harmless SAPRES TECHNOLOGIES and/or the SAPRES TECHNOLOGIES Customer against any and all claims of third parties arising from such proprietary rights (including, but not limited to the violation of copyrights and patents). The Contractor shall indemnify SAPRES TECHNOLOGIES and/or the SAPRES TECHNOLOGIES Customer against all payments for damages and / or other liabilities.</p>
                <p>(6) Any Party shall without delay inform the other Party of any claims made by any third party alleging a violation of rights relating to the use of any results in connection with the services carried out by the Contractor.</p>
                <p>(7) Furthermore, the Contractor shall either substitute the results or make changes to the results so that proprietary rights of any third party, including but not limited to copyrights, are no longer violated or shall provide a licence granting the right to use such results, which gave rise to such third party objections.</p>
                <p>(8) This will be without prejudice to any other contractual or statutory rights of SAPRES TECHNOLOGIES in connection with the violation of proprietary rights.</p>"""
    )

    non_disclosure_obligation = fields.Html(
        string="Non-Disclosure Obligation",
        default="""<p>(1) The Contractor shall – without limitation of time - treat as confidential and not disclose to any third party any information and trade secrets of SAPRES TECHNOLOGIES and/or SAPRES TECHNOLOGIES&apos;s Customer obtained during the execution of his duties and shall use such information solely for the execution of such duties.</p>
                <p>(2) The Contractor shall not disclose to any third party any information in connection with the subject matter of this Agreement or of any DOS.</p>
                <p>(3) Upon completion of the services or termination of the DOS, the Contractor shall – without delay – hand over to SAPRES TECHNOLOGIES all documents produced during the execution of his duties and return all material provided by either SAPRES TECHNOLOGIES or SAPRES TECHNOLOGIES&apos;s Customer. The Contractor shall not be entitled to withhold any documents or copies or notes of any documents produced in connection with services carried out under a DOS.</p>
                <p>(4) The Contractor shall observe all relevant statutory provisions including, but not limited to those laid down in the Federal Data Protection Act (Bundesdatenschutzgesetz) and Telecommunications Act (Fernmeldegesetz). He shall, in particular, keep such information confidential and not disclose such information to any unauthorised third party . </p>"""
    )

    handover = fields.Html(
        string="Handover",
        default="""<p>(1) If and as far as the DOS contains any provisions on handover agreed between SAPRES TECHNOLOGIES and SAPRES TECHNOLOGIES&apos;s Customer such provisions shall apply in addition to any statutory handover provisions.</p>"""
    )

    warranty_damages = fields.Html(
        string="Warranty, Damages",
        default="""<p>(1) If a DOS contains elements of works the warranty period for such works shall be 24 months from the date of acceptance. In all other respects the statutory provisions shall apply.</p>
                <p>(2) If and as far as the acceptance of works carried out by the Contractor does not coincide in time with the acceptance of works between SAPRES TECHNOLOGIES and SAPRES TECHNOLOGIES Customer, the warranty period shall be 12 months from the unreserved handover of SAPRES TECHNOLOGIES&apos;s Customer.</p>"""
    )

    request_for_changes = fields.Html(
        string="Request for Changes",
        default="""<p>(1) Unless and until the Contractor has not completely carried out his services, SAPRES TECHNOLOGIES is entitled to request changes in writing. The Contractor shall make such changes unless such changes unreasonably exceed the Contractor&apos;s operational capacity.</p>
                <p>(2) If these changes affect the contractual terms and conditions (e.g. minimum/maximum remuneration/fee, deadlines, handover, acceptance, terms), the Parties shall without delay adjust the relevant contractual terms and conditions in writing. Immaterial changes may be disregarded.</p>
                <p>(3) If the examination of such request for changes requires a considerable effort in time, the Parties shall upon the request of the Contractor agree on separate instructions for such examination, which determine the remuneration/fee as well as the completion dates for the submission of such examination including the impact on the contractual terms and conditions.</p>
                <p>(4) SAPRES TECHNOLOGIES is entitled to demand from the Contractor an interruption of the services or parts thereof until a decision on the execution of such changes is reached. For any downtimes as a result of any such demand the Contractor shall be appropriately compensated if and to the extent that the Contractor cannot be assigned to any other works/services. Upon the request of the Contractor the contractual deadlines and due dates for his services shall be adjusted upon giving due regard to any downtime.</p>
                <p>(5) If the Contractor does not within ten days from receiving the request for changes state in writing whether or to what extent it is unreasonable for him to carry out such changes or does not request in writing separate instructions for such examination or does not request any change of the existing contractual terms and conditions, which he considers necessary, the Contractor shall provide the requested services on the basis of this Agreement and DOS.</p>
                <p>(6) If an adjustment of the contractual terms and conditions does not come into effect within four weeks from SAPRES TECHNOLOGIES&apos;s request for such adjustment, the services shall be continued without considering such request for changes.</p>"""
    )

    customer_protection = fields.Html(
        string="Customer Protection",
        default="""<p>(1) If SAPRES TECHNOLOGIES involves the Contractor in concrete marketing or negotiations with the view to win any SAPRES TECHNOLOGIES Customer, the Contractor shall for a duration of 24 months from completion of any services not directly or indirectly engage in any competing activities vis-à-vis any SAPRES TECHNOLOGIES Customer unless SAPRES TECHNOLOGIES expressly agrees to any such activity in writing.</p>
                <p>(2) The Contractor shall not provide any proposal and/or quotation to any SAPRES TECHNOLOGIES Customer. Furthermore, the Contractor shall not make any contribution of any kind to any third party which intends to make an offer competing with any DOS or which have already made any such offer.</p>
                <p>(3) During the term of any DOS and for a period of 24 months from the completion of any such services the Contractor shall not directly or indirectly engage in any activities competing with SAPRES TECHNOLOGIES&apos;s relations to SAPRES TECHNOLOGIES Customer. The Contractor shall not engage in any activity vis-à-vis any SAPRES TECHNOLOGIES Customer whereby such activities would directly or indirectly compete with activities as set out in the DOS or in any modification and/or extension agreement thereof. Unless expressly agreed by SAPRES TECHNOLOGIES in writing, the Contractor shall not directly or indirectly engage in any activity for any such third party which offers services to SAPRES TECHNOLOGIES&apos;s Customer which are identical or similar to services contained in any DOS.</p>
                <p>(4) The Contractor shall - during and after completion of his services - not make any direct or indirect contact with SAPRES TECHNOLOGIES&apos;s Customer with respect to any terms and conditions set out in any DOS, modification or extension agreement thereof.</p>
                <p>(5)The Contractor shall ensure that his employees and subcontractors strictly comply with the aforementioned obligations. If the Contractor violates any of the aforementioned obligations, the Contractor shall pay to SAPRES TECHNOLOGIES a contractual penalty of 25.000,-- EURO for each violating incident. SAPRES TECHNOLOGIES reserves the right to demand further damages over and above the aforementioned contractual penalty. </p>
                <p>(6) SAPRES TECHNOLOGIES will exempt the Contractor from the obligation to observe Customer Protection vis-à-vis any particular customer, if SAPRES TECHNOLOGIES terminates or discontinues the contractual and/or business relationship with such SAPRES TECHNOLOGIES Customer and no further legitimate interest in the protection of such SAPRES TECHNOLOGIES Customer exists. Any termination of Customer Protection must be made by SAPRES TECHNOLOGIES in writing in order to valid.</p>"""
    )
    non_solicitation_obligation = fields.Html(
        string="Non-Solicitation Obligation",
        default="""<p>(1)Each Party - during the services carried out under this Agreement and for a period of twenty-four (24) months from the completion of such services - hereby undertakes not to directly or indirectly entice away any employee of the other Party or any person engaged in any way by such other Party in the execution of duties arising from this Agreement </p>"""
    )

    liability = fields.Html(
        string="Liability",
        default="""<p>(1) The Contractor comply with any statutory rules and regulations.</p>
        <p>(2) The Parties agree that this Agreement and any respective DOS are considered to be subcontracts. During the term of the contractual relation, the Contractor shall provide SAPRES TECHNOLOGIES with sufficient and exhaustive information about his self-employed status. If an examination by any third party should determine that the Contractor is considered to be employees of SAPRES TECHNOLOGIES or SAPRES TECHNOLOGIES Customer, e.g. due to non-compliance with legislation concerning a self-employment sham, the Contractor shall fully indemnify and hold harmless SAPRES TECHNOLOGIES against any damages arising therefrom..</p>"""
    )

    personnel_data = fields.Html(
        string="Handling and Storage of Personnel Data",
        default="""<p>(1) The Contractor agrees that SAPRES TECHNOLOGIES may collect its personal data which are required by SAPRES TECHNOLOGIES for the execution of its duties and that it may process and store such data in a machine-readable or other form and that it may analyse such data and provide such data or analyses to any SAPRES TECHNOLOGIES Customer concerned.</p>
        <p>(2) This includes, but is not limited to, information suitable for an evaluation of the performance quality of the assigned employee, including, but not limited to information on special expertise, sector/trade knowledge, project experience, product knowledge, language skills as well as SAPRES TECHNOLOGIES Customer-specific knowledge.</p>"""
    )

    contract_term_termination = fields.Html(
        string="Contract Term and Termination",
        default="""<p>(1) This Agreement shall come into force upon signing by SAPRES TECHNOLOGIES and the Contractor and shall run for an indefinite period of time. This Agreement may be terminated in writing by either Party upon observing a three months&apos; notice period to the end of a calendar quarter. In case of a termination of this Agreement, all DOS concluded prior to the termination of this Agreement shall remain unaffected and unchanged, unless otherwise agreed by the Parties in writing. Provisions of this Agreement shall remain incorporated in any DOS concluded under this Agreement and continue to be valid until the end of any such DOS.</p>
        <p>(2) SAPRES TECHNOLOGIES is entitled to terminate the respective DOS by observing a three months&apos; notice period.</p>
        <p>(3) If a project cannot be continued as the contractual relations between SAPRES TECHNOLOGIES and SAPRES TECHNOLOGIES Customer are terminated or cancelled or come to an end in any other way, SAPRES TECHNOLOGIES is entitled to terminate the respective DOS with the Contractor upon giving a 14 days notice.</p>
        <p>(4) In cases pursuant to clause 15 subclause (2) and (3) a claim for remuneration by the Contractor will expire upon the date on which the termination takes effect. To that extent section 649 German Civil Code shall be waived. Any services carried out by the Contractor prior to the date on which the termination takes effect will be charged according to the provisions of the relevant DOS.</p>
        <p>(5) Furthermore, in case of a termination of a DOS, the Contractor shall document the results achieved and shall hand over to SAPRES TECHNOLOGIES this documentation in an electronically suitable form (data media) and/or hardcopy, together with any other documents no later than on the date on which the termination takes effect.</p>
        <p>(6) The right of termination for a serious reason (&quot;wichtiger Grund&quot;) by either Party remains unaffected.</p>"""
    )

    final_clauses = fields.Html(
        string="Final Clauses",
        default="""<p>(1) This Agreement is binding upon the Parties. Each Party ensures that this Agreement is also binding upon those companies in which such Party holds a majority interest/participation.</p>
        <p>(2) Any changes and/or supplements to this Agreement must be made in writing. Such written form requirement shall likewise apply to a rescission and/or a waiver of this written form requirement. The Parties confirm that they have not entered into any ancillary or oral agreements.</p>
        <p>(3) Should any provision of this Agreement or of any DOS be or become invalid or unenforceable, such provision shall be without prejudice to the validity of the remaining provisions of this Agreement or of any DOS. The Parties hereby agree to replace any invalid or unenforceable provision by a valid and enforceable provision which reflects as closely as possible the economic objective of the Parties. The same shall apply in the event of an omission.</p>
        <p>(4) This Agreement shall be governed exclusively by the laws of the Federal Republic of Germany.</p>
        <p>(5) The place of jurisdiction is Darmstadt, Germany.</p>"""
    )
    project_organization = fields.Html(
        string="Project Organization",
        default="""<p>SAPRES appoints Mr Selim Ben Yedder as project manager entitled to representation.</p>
            <p>The Project Director informs the Consultant on the resp. current project schedule, lays down the tasks to be performed and the specifications to be adhered to by the latter, in particular the target dates and planning costs (in man days).</p>
        <p>The Consultant reports to the Project Director on the progress of the works at regular intervals of not less than once a month.</p>"""
    )
    ginsheim = fields.Date(string="Master Agreement Date")
    frankfurt = fields.Date(string="Service Agreement Date ")
    day_rate_site = fields.Float(string="Day Rate for onsite ")
    day_rate_remote = fields.Float(string="Day Rate for onsite ")
    client_order_ref = fields.Char(string='Contract Number', copy=False)



    def write(self, vals):
        for order in self:
            # Priorité : date dans vals sinon existante
            date_val = vals.get('date') or order.date

            if isinstance(date_val, date):
                date_str = date_val.strftime('%Y-%m-%d')
                date_str_ = date_val.strftime('%m-%Y')
            else:
                date_str = str(date_val)
                date_str_ = str(date_val)

            # Ne modifier contract_no que si pas explicitement fourni
            if 'contract_no' not in vals and 'date' in vals:
                vals['contract_no'] = f'SERVICE_{date_str}'
            if 'client_order_ref' not in vals and 'date' in vals:
                vals['client_order_ref'] = f'{date_str_}_Master'

        return super(PurchaseOrder, self).write(vals)
    @api.depends('order_line', 'order_line.vendor_id')
    def update_multi_vendor_id(self):
        for order in self:
            order.multi_vendor_id = [(6, 0, order.order_line.mapped('vendor_id').ids)]

    new_name = fields.Char('Order Reference', required=True, index=True, copy=False, default='New')
    client_order_ref = fields.Char(string='Contract Number', copy=False)
    date = fields.Date('Start Date', required=True, index=True, default=fields.Date.context_today)
    datas = fields.Many2many('ir.attachment', 'doc_attach_rel', 'doc_id', 'attach_id3', string="Attachment",
                             help='You can attach the copy of your document', copy=False)
    end_date = fields.Date('End Date', required=False, index=True)
    quantity_by_day = fields.Float('PO Unit')
    number_of_hour_by_day = fields.Float('Daily hours', default=8.0)
    totol_hours = fields.Float('PO Unit')
    contract_type = fields.Selection([
        ('d', 'Days'),
        ('h', 'Hour'),
    ], string="PO", )
    description = fields.Text(string='Description', copy=False)
    vendor_id = fields.Many2one('res.partner', string="Consultant", required=False)
    Signature = fields.Selection([
        ('double', 'Double'),
        ('sapres', 'Sapres'),
        ('consultant', 'Consultant'),
    ], string="Signature")
    order_id = fields.Many2one('sale.order', compute='action_sale_orders', store=True)
    tasks_ids = fields.Many2many('project.task', compute='_compute_tasks_ids', string='Tasks associated to this sale')
    tasks_count = fields.Integer(string='Tasks', compute='_compute_tasks_ids', groups="project.group_project_user")

    project_count = fields.Integer(string='Number of Projects', compute='_compute_project_ids',
                                   groups='project.group_project_manager')
    project_ids = fields.Many2many('project.project', compute="_compute_project_ids", string='Projects', copy=False,
                                   groups="project.group_project_manager", help="Projects used in this sales order.")
    timesheet_total_duration = fields.Integer("Timesheet Total Duration", compute='_compute_timesheet_total_duration',
                                              help="Total recorded duration, expressed in the encoding UoM, and rounded to the unit")
    timesheet_encode_uom_id = fields.Many2one('uom.uom', related='company_id.timesheet_encode_uom_id')
    timesheet_ids = fields.Many2many('account.analytic.line', compute='_compute_timesheet_ids',
                                     string='Timesheet activities associated to this sale')
    timesheet_count = fields.Float(string='Timesheet activities', compute='_compute_timesheet_ids')
    tcs = fields.Boolean(string='TCS', default=False)
    new_name = fields.Char('Reference', required=True, index=True, copy=False, default='New')

    @api.model
    def create(self, vals):
        company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
        # Ensures default picking type and currency are taken from the right company.
        self_comp = self.with_company(company_id)

        if vals.get('name', 'New') == 'New':
            seq_date = None
            # Vérifier si 'date_order' est dans vals avant de l'utiliser
            if 'date_order' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            vals['name'] = self_comp.env['ir.sequence'].next_by_code('purchase.order', sequence_date=seq_date) or '/'

        vals, partner_vals = self._write_partner_values(vals)

        # Call the parent class's create method using super
        res = super(PurchaseOrder, self_comp).create(vals)

        if partner_vals:
            res.sudo().write(partner_vals)

        # Vérifier si 'date_order' est dans vals avant de l'utiliser
        current_year = datetime.datetime.now().year

        # Extracting the last three characters of vals['name'] as new_id
        new_id = vals['name'][-4:]

        # Update the 'new_name' field with the desired value
        if 'partner_id' in vals:
            partner = self_comp.env['res.partner'].browse(vals['partner_id'])
            if partner:
                test = partner.id
                res.new_name = f"{current_year}_{test}_{new_id}"

        return res

    @api.depends('order_line.sale_order_id')
    def action_sale_orders(self):
        for rec in self.order_line.sale_order_id:
            order_field = rec
            self.order_id = order_field.id

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        invoice_vals['vendor_id'] = self.vendor_id.id
        return invoice_vals

    @api.onchange('contract_type')
    def _onchange_contract_type_hours(self):
        for rec in self:
            if rec.contract_type == 'h':
                rec.totol_hours = 0.0

    @api.onchange('contract_type')
    def _onchange_contract_type_days(self):
        for rec in self:
            if rec.contract_type == 'd':
                rec.number_of_hour_by_day = 8.0
                rec.quantity_by_day = 0.0

    @api.onchange('quantity_by_day', 'number_of_hour_by_day')
    def _onchange_totol_hour(self):
        for rec in self:
            rec.totol_hours = rec.quantity_by_day * rec.number_of_hour_by_day

    @api.onchange('end_date')
    def _onchange_end_date(self):
        for rec in self:
            rec.validity_date = rec.end_date

    @api.onchange('date')
    def _onchange_end_date(self):
        for rec in self:
            rec.date_order = rec.date

    @api.constrains('date', 'end_date')
    def _check_contract_date(self):
        for event in self:
            if event.end_date and event.date:
                if event.end_date < event.date:
                    raise ValidationError(_('The closing date cannot be earlier than the beginning date.'))

    @api.onchange('order_line')
    def _onchange_number_of_hour_by_day(self):
        for rec in self:
            for line in rec.order_line:
                rec.number_of_hour_by_day = line.number_of_hour_by_day

    def action_view_timesheet(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("sale_timesheet.timesheet_action_from_sales_order")
        action['context'] = {
            'search_default_billable_timesheet': True
        }  # erase default filters
        if self.timesheet_count > 0:
            print('action', action)
            action['domain'] = [('consultant_id', '=', self.partner_id.id),
                                ('so_line', 'in', self.order_id.order_line.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.depends('order_id')
    def _compute_timesheet_total_duration(self):
        for order in self:
            order.timesheet_total_duration = order.order_id.timesheet_total_duration

    @api.depends('order_id', 'partner_id')
    def _compute_timesheet_ids(self):
        for order in self:
            matching_timesheet_ids = []
            for line in order.order_id.timesheet_ids:
                if line.consultant_id.id == order.partner_id.id:
                    matching_timesheet_ids.append(line.id)
            order.timesheet_ids = [(6, 0, matching_timesheet_ids)]
            order.timesheet_count = order.order_id.timesheet_count

    @api.depends('order_id')
    def _compute_project_ids(self):
        for order in self:
            order.project_count = order.order_id.project_count
            order.project_ids = order.order_id.project_ids

    def action_view_project_ids(self):
        self.ensure_one()
        view_form_id = self.env.ref('project.edit_project').id
        view_kanban_id = self.env.ref('project.view_project_kanban').id
        action = {
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.project_ids.ids)],
            'view_mode': 'kanban,form',
            'name': _('Projects'),
            'res_model': 'project.project',
        }
        if len(self.project_ids) == 1:
            action.update({'views': [(view_form_id, 'form')], 'res_id': self.project_ids.id})
        else:
            action['views'] = [(view_kanban_id, 'kanban'), (view_form_id, 'form')]
        return action

    @api.depends('order_id')
    def _compute_tasks_ids(self):
        for line in self:
            line.tasks_count = line.order_id.tasks_count
            line.tasks_ids = line.order_id.tasks_ids

    def action_view_task(self):
        self.ensure_one()
        list_view_id = self.env.ref('project.view_task_tree2').id
        form_view_id = self.env.ref('project.view_task_form2').id

        action = {'type': 'ir.actions.act_window_close'}
        task_projects = self.tasks_ids.mapped('project_id')
        if len(task_projects) == 1 and len(
                self.tasks_ids) > 1:  # redirect to task of the project (with kanban stage, ...)
            action = self.with_context(active_id=task_projects.id).env['ir.actions.actions']._for_xml_id(
                'project.act_project_project_2_project_task_all')
            action['domain'] = [('id', 'in', self.tasks_ids.ids)]

            if action.get('context'):
                eval_context = self.env['ir.actions.actions']._get_eval_context()
                eval_context.update({'active_id': task_projects.id})
                action_context = safe_eval(action['context'], eval_context)
                action_context.update(eval_context)
                action['context'] = action_context

        else:
            action = self.env["ir.actions.actions"]._for_xml_id("project.action_view_task")
            action['context'] = {}  # erase default context to avoid default filter
            if len(self.tasks_ids) > 1:  # cross project kanban task
                action['views'] = [[False, 'kanban'], [list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'],
                                   [False, 'calendar'], [False, 'pivot']]
            elif len(self.tasks_ids) == 1:  # single task -> form view
                action['views'] = [(form_view_id, 'form')]
                action['res_id'] = self.tasks_ids.id
        # filter on the task of the current SO
        action.setdefault('context', {})
        action['context'].update({'search_default_order_id': self.id})

        return action

    @api.onchange('timesheet_ids')
    def sale_user_id_onchange(self):
        for rec in self.timesheet_ids:
            if rec.consultant_id:
                print('domain', {'domain': {'consultant_id': [('consultant_id', '=', self.partner_id.id)]}})
                return {'domain': {'consultant_id': [('consultant_id', '=', self.partner_id.id)]}}


class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    discount = fields.Float('Discount %')
    number_of_hour_by_day = fields.Float('Daily hours', default=8.0)
    service_type = fields.Selection([
        ('mixte', 'Mixte'),
        ('site', 'On Site'),
        ('romote', 'Remote'),
    ], string="Service Type")
    vendor_id = fields.Many2one('res.partner', string="Consultant", required=False)
    tcs_ba_id = fields.Char(string='TCS BA ID', default="")
    date = fields.Date('Start Date', required=False, index=True)
    end_date = fields.Date('End Date', required=False, index=True)

    def _prepare_compute_all_values(self):
        discount = (self.price_unit * self.discount * self.product_qty) / 100
        self.ensure_one()
        return {
            'price_unit': self.price_unit - discount,
            'currency': self.order_id.currency_id,
            'quantity': self.product_qty,
            'product': self.product_id,
            'partner': self.order_id.partner_id,
        }

    def _prepare_account_move_line(self, move=False):
        result = super(purchase_order_line, self)._prepare_account_move_line()
        if result:
            result.update({
                'discount': self.discount,
                'service_type': self.service_type,
                'tcs_ba_id': self.tcs_ba_id,
            })
        return result








