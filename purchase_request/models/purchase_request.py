from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


class Purchase_Request(models.Model):
    _name = "purchase.request"
    _description = "Purchase Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string='Name', required=True, readonly=True, index=True, default=lambda self: _('New'))
    requested_by = fields.Many2one(comodel_name="res.users", required=True, copy=False, tracking=True,
                                   default=lambda self: self.env.user, index=True)
    vendor = fields.Many2one(comodel_name="res.users", string="Vendor", tracking=True)
    start_date = fields.Date(string="Start Date", default=fields.Date.context_today, store=True, tracking=True)
    end_date = fields.Date(string="End Date")
    rejection_reason = fields.Text("Rejection Reason")
    order_lines = fields.One2many(comodel_name="purchase.request.line", inverse_name="request_id", string="Order lines",
                                  readonly=False, copy=True)
    total_Price_qnt = fields.Integer(compute="compute_total_price", string="Total Price")

    state = fields.Selection([
        ("draft", "Draft"),
        ("to_approve", "To be approved"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("cancel", "Cancel"),
     ], default='draft', string='state', copy=False)

    @api.depends("order_lines", "order_lines.total")
    def compute_total_price(self):
        for rec in self:
            rec.total_Price_qnt = sum(rec.order_lines.total)

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for date in self:
            # Starting date must be prior to the ending date
            date_from = date.start_date
            date_to = date.end_date
            if date_to < date_from:
                raise ValidationError(_('The ending date must not be prior to the starting date.'))

    @api.model
    def create(self, vals):
        if 'name' not in vals or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.request') or _('New')
        return super(Purchase_Request, self).create(vals)

    def btn_reset_to_draft(self):
        return self.write({"state": "approved"})

    def btn_submit_for_approval(self):
        return self.write({"state": "to_approve"})

    def btn_approve(self):
        self.state = 'approved'
        q_group = self.env.ref('purchase.group_purchase_manager')
        recipient_ids = [user.partner_id.id for user in q_group.users]
        emails = ""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        action = self.env.ref('purchase_request.purchase_request_form_action').id
        base_url += '/web#id=%d&view_type=form&action=%d&model=%s' % (self.id, action, self._name)
        for user in q_group.users:
            emails += "%s," % user.partner_id.email
            author = self.env.user.partner_id
            subject = _('Purchase Request has been approved')
            subject = '''Purchase Request {}'''.format(self.name)
            body = "%s," % base_url
            body = '''
                   <div style="font-size: small;">
                       Dear ,
                       Kindly check Purchase Request <a href="{}"> <span style="color: red;">
                         here
                        </span></a>
                        has been approved
                   '''.format(
                base_url,
            )
            self._send_notification(recipient_ids, emails, author, subject, body)

    def _send_notification(self, recipient_ids, emails, author, subject, body):
        email_from = author.email_formatted
        mail_content = {
            'subject': subject,
            'body_html': body,
            'body': body,
            'is_notification': True,
            'email_to': emails,
            'email_from': email_from,
            'reply_to': email_from,
            'recipient_ids': recipient_ids,
            'message_type': 'email',
            'author_id': author.id,
            'res_id': self.id,
            # 'model': 'commercial.offer'
        }
        mail = self.env['mail.mail'].sudo().create(mail_content)
        mail.send()
        for u_id in recipient_ids:
            self.env['mail.notification'].sudo().create({
                'res_partner_id': u_id,
                'mail_message_id': mail.mail_message_id.id
            })


class Purchase_Request_Line(models.Model):
    _name = "purchase.request.line"
    _description = "Purchase Request Line"

    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=True)
    name = fields.Char(string="Description", tracking=True)
    quantity = fields.Float(string="Quantity", default=1)
    request_id = fields.Many2one(comodel_name="purchase.request", string="Purchase Request", ondelete="cascade",
                                 readonly=True, index=True, auto_join=True)
    cost_price = fields.Float(related='product_id.list_price')
    price = fields.Float(string="price", tracking=True, default=1)

    total = fields.Float(comput="compute_total", string="Total", readonly=True)

    @api.depends("quantity", "price")
    def compute_total(self):
        for rec in self:
            rec.total = (rec.quantity * rec.price)
            print("total ", rec.total)

    @api.onchange("product_id")
    def onchange_product_id(self):
        if self.product_id:
            name = self.product_id.name
            self.quantity = 1
            self.name = name
