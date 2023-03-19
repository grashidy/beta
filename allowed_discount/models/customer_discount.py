# -*- coding: utf-8 -*-

import dateutil.utils
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from datetime import datetime


class ResPartner(models.Model):
    _inherit = "res.partner"

    allowed_discount = fields.Float(string="Allowed Discount %")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    allowed_discount = fields.Float(related="partner_id.allowed_discount", string="Allowed Discount %")

    @api.onchange("partner_id")
    def partner_id_change(self):
        if self.partner_id and self.allowed_discount > 0:
            product_id = self.env['ir.config_parameter'].sudo().get_param('allowed_discount.discount_product')
            print(int(product_id))
            order_lines = []
            for rec in self:
                rec.allowed_discount = rec.partner_id.allowed_discount
                order_lines.append = (0, 0, {
                    'product_id': int(product_id),
                    'name': product_id,
                    'product_uom_qty': 1,
                    'price_unit': rec.allowed_discount * -1,
                    'order_id': rec.id
                })

                rec.order_line = order_lines
                print(len(order_lines))


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"


class AccountMove(models.Model):
    _inherit = "account.move"

    allowed_discount = fields.Float(related="partner_id.allowed_discount", string="Allowed Discount %")

    @api.onchange("partner_id")
    def set_default_discount(self):
        self.allowed_discount = self.partner_id.allowed_discount
        if self.partner_id and self.allowed_discount > 0:
            account_id = self.env['ir.config_parameter'].sudo().get_param('allowed_discount.discount_account')


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    allowed_discount_product = fields.Many2one(comodel_name='product.product',
                                               domain=[('detailed_type', '=', 'service')],
                                               config_parameter='allowed_discount.discount_product',
                                               string='Allowed Discount Product ', required=True)
    allowed_discount_account = fields.Many2one(comodel_name='account.account',
                                               string='Allowed Discount Account ', required=True,
                                               config_parameter='allowed_discount.discount_account', )
