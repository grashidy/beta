from odoo import _, api, exceptions, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    request_line_ref = fields.Many2one("purchase.request.line", string="request Reference")


