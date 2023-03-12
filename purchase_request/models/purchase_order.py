import dateutil.utils
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from datetime import datetime


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    request_line_ref = fields.Many2one("purchase.request.line", string="request Reference")

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        order_obj = []
        req_obj = []
        req_qty = 0.0
        order_qty = 0.0
        conf_qty = 0.0
        order_qty = self.product_qty
        max_qty = self._origin.product_qty
        req_obj = self.env["purchase.request.line"].search(
            [("id", "=", self.request_line_ref.id)]
        )
        req_qty = req_obj.quantity
        req_ids = self.env['purchase.request'].search([('line_ids.request_id', '=', req_obj.request_id.id)])
        len_order = len(req_ids)
        confirmed_orders = self.env["purchase.order"].search([('origin', '=', req_obj.request_id.name),
                                                              ('state', '=', 'purchase'),
                                                              ])
        order_obj = confirmed_orders.order_line.filtered(lambda x: x.product_id == self.product_id)
        conf_qty = sum(order_obj.mapped("product_qty"))
        max_qty = req_qty - conf_qty

        if len(req_obj) >= 1 and max_qty >= 1:
            if order_qty > max_qty:
                self.product_qty = max_qty
                raise UserError(_("the max allowed qty %s", max_qty))
                return {}
            sup = super(PurchaseOrderLine, self)._onchange_quantity()
            self.product_qty = order_qty
            return sup
        else:
            return {}
