import dateutil.utils
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from datetime import datetime


class Purchase_Request(models.Model):
    _name = "purchase.request"
    _description = "Purchase Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string='Name', required=True, readonly=True, index=True, default=lambda self: _('New'))
    requested_by = fields.Many2one(comodel_name="res.users", required=True, copy=False, tracking=True,
                                   default=lambda self: self.env.user, index=True)
    vendor = fields.Many2one(comodel_name="res.partner", string="Vendor", tracking=True)
    start_date = fields.Date(string="Start Date", default=fields.Date.context_today, store=True, tracking=True)
    end_date = fields.Date(string="End Date")
    rejection_reason = fields.Text("Rejection Reason")
    line_ids = fields.One2many(comodel_name="purchase.request.line", inverse_name="request_id",
                               string="Request lines", readonly=False, copy=True)
    total_Price_qnt = fields.Integer(compute="compute_total_price", string="Total Price")
    order_count = fields.Integer(compute="compute_purchase_order_count", string="Total Price")

    state = fields.Selection([
        ("draft", "Draft"),
        ("to_approve", "To be approved"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("cancel", "Cancel"),
    ], default='draft', string='state', copy=False)

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for date in self:
            if date.end_date:
                date_from = date.start_date
                date_to = date.end_date
                if date_to < date_from:
                    raise ValidationError(_('The ending date must not be prior to the starting date.'))

    @api.depends('line_ids')
    def compute_purchase_order_count(self):
        for orders in self:
            order_ids = self.env['purchase.order'].search([('origin', '=', self.name)])
        self.order_count = len(order_ids)

    @api.depends("line_ids")
    def action_po_count(self):
        return

    @api.depends('line_ids.total')
    def compute_total_price(self):
        for rec in self:
            rec.total_Price_qnt = sum(rec.line_ids.mapped("total"))

    @api.model
    def create(self, vals):
        if 'name' not in vals or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.request') or _('New')
        return super(Purchase_Request, self).create(vals)

    def btn_reset_to_draft(self):
        self.state = "approved"

    def btn_submit_for_approval(self):
        self.state = "to_approve"

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

    def action_purchase_order_creation(self):
        for request in self:
            lines = request.line_ids
            purchase_order_id = self.env['purchase.order'].sudo().create({
                'name': request.name,
                'purchase_request_line_ids': lines.ids
            })

    def action_open_purchase_order(self):
        self.ensure_one()
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        action['domain'] = [('origin', '=', self.name)]
        return action

    def action_view_purchase_order(self):
        action = self.env.ref("purchase.purchase_rfq").read()[0]
        lines = self.mapped("line_ids")
        print(lines)
        action["domain"] = [('origin', '=', self.name)]
        action["name"] = ("purchase Order")
        view_id = self.env.ref("purchase_request_view_form").id
        action.update(
            views=[(view_id, "form")],
        )
        action["context"] = {
            'origin': self.name,
            'date_order': fields.date.today(),
            'name': self.name,
            'partner_id': self.vendor.id,
            "order_line": lines,
        }
        return action

    def btn_view_rfq(self):
        for rec in self:
            if len(rec.line_ids) >= 1:
                po_obj = self.env['purchase.order']
                confirmed_orders = []
                confirmed_orders = po_obj.search([('origin', '=', rec.name), ('state', '=', 'purchase')])
                count = len(confirmed_orders)
                print(count)
                print(confirmed_orders.mapped("origin"))
                p_order_qty = 0.0
                order_qty_sum = 0.0
                req_qty_sum = 0.0
                line_ids = []
                for line in rec.line_ids:
                    order_product = confirmed_orders.order_line.filtered(lambda x: x.product_id == line.product_id)
                    print(order_product.mapped("product_qty"))
                    order_qty_sum = sum(order_product.mapped("product_qty"))
                    print(order_qty_sum)
                    req_qty_sum = sum(line.quantity for line in line)
                    print(req_qty_sum)
                    if req_qty_sum > order_qty_sum:
                        p_order_qty = req_qty_sum - order_qty_sum
                    print(p_order_qty)
                    if p_order_qty > 0:
                        line_ids.append((0, 0, {
                            'name': line.name,
                            'product_id': line.product_id.id,
                            'product_uom': line.product_uom.id,
                            'date_planned': fields.date.today(),
                            'product_qty': p_order_qty,
                            'price_unit': line.price,
                            'request_line_ref': line.id,
                        }))

                return {
                    'name': _("RFQ"),
                    'view_mode': 'form,tree',
                    'res_model': 'purchase.order',
                    'view_id': False,
                    'context': {
                        'default_origin': rec.name,
                        'default_date_order': fields.date.today(),
                        'default_name': rec.name,
                        'default_partner_id': rec.vendor.id,
                        'default_order_line': line_ids,
                    },
                    'type': "ir.actions.act_window",
                    'target': 'new',
                    'create': False,
                }
            else:
                raise UserError(_("Please select a product!"))

    def btn_create_rfq(self):
        for rec in self:
            if len(rec.line_ids) >= 1:
                po_obj = self.env['purchase.order']
                confirmed_orders = []
                confirmed_orders = po_obj.search([('origin', '=', rec.name), ('state', '=', 'purchase')])
                count = len(confirmed_orders)
                print(count)
                print(confirmed_orders.mapped("origin"))
                p_order_qty = 0.0
                order_qty_sum = 0.0
                req_qty_sum = 0.0
                line_ids = []
                for line in rec.line_ids:
                    order_product = confirmed_orders.order_line.filtered(lambda x: x.product_id == line.product_id)
                    print(order_product.mapped("product_qty"))
                    order_qty_sum = sum(order_product.mapped("product_qty"))
                    print(order_qty_sum)
                    req_qty_sum = sum(line.quantity for line in line)
                    print(req_qty_sum)
                    if req_qty_sum > order_qty_sum:
                        p_order_qty = req_qty_sum - order_qty_sum
                    print(p_order_qty)
                    if p_order_qty > 0:
                        line_ids.append((0, 0, {
                            'name': line.name,
                            'product_id': line.product_id.id,
                            'product_uom': line.product_uom.id,
                            'date_planned': fields.date.today(),
                            'product_qty': p_order_qty,
                            'price_unit': line.price,
                            'request_line_ref': line.id,
                        }))
                purchase_order_id = self.env['purchase.order'].sudo().create({
                    'name': 'New',
                    'origin': self.name,
                    'date_order': fields.date.today(),
                    'partner_id': self.vendor.id,
                    'order_line': line_ids,
                        })
                return {
                    'name': _("RFQ"),
                    'view_mode': 'form,tree',
                    'res_model': 'purchase.order',
                    'view_id': False,
                    'context': {
                        'default_origin': rec.name,
                        'default_date_order': fields.date.today(),
                        'default_name': rec.name,
                        'default_partner_id': rec.vendor.id,
                        'default_order_line': line_ids,
                    },
                    'type': "ir.actions.act_window",
                    'target': 'new',
                    'create': False,
                }
            else:
                raise UserError(_("Please select a product!"))



class Purchase_Request_Line(models.Model):
    _name = "purchase.request.line"
    _description = "Purchase Request Line"

    purchase_id = fields.Many2one(string='Request Reference', required=False, ondelete='cascade',
                                  index=True, copy=False, invisible=1)
    product_id = fields.Many2one(comodel_name="product.product", string="Product", required=True)
    name = fields.Char(string="Description", tracking=True)
    quantity = fields.Float(string="Quantity", default=1)
    product_uom = fields.Many2one(comodel_name="uom.uom", string="Unit Measure", tracking=True,
                                  domain="[('category_id', '=', uom_category)]",
                                  )
    uom_category = fields.Many2one(related="product_id.uom_po_id.category_id")

    request_id = fields.Many2one(comodel_name="purchase.request", string="Purchase Request", ondelete="cascade",
                                 readonly=True, index=True, auto_join=True)
    cost_price = fields.Float(related='product_id.list_price')
    price = fields.Float(string="price", tracking=True, default=1)
    total = fields.Float(compute="compute_total", string="Total", readonly=True)

    @api.depends("quantity", "price")
    def compute_total(self):
        for rec in self:
            rec.update({
                'total': (rec.quantity * rec.price)
            })

    @api.onchange("product_id")
    def onchange_product_id(self):
        if self.product_id:
            name = self.product_id.name
            self.product_uom = self.product_id.uom_id.id
            self.quantity = 1
            self.name = name
