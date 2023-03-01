

from odoo import _, api, exceptions, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    purchase_lines = fields.Many2one(comodel_name="purchase.request.line",
                                             tracking=True)

