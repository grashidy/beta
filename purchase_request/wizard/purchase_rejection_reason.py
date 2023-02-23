# -*- coding: utf-8 -*-

##############################################################################

from odoo.exceptions import ValidationError
from odoo import api, fields, models, _


class PurchaseRejectionReasonWizard(models.TransientModel):
    _name = "purchase.rejection.reason.wizard"
    _description = 'Purchase Rejection Reason Wizard'

    name = fields.Text(string='Name', required=True)

    def btn_confirm(self):
        active_id = self._context.get('active_id')
        purchase_obj = self.env['purchase.request'].browse(active_id)
        vals = {
            "rejection_reason": self.name,
            "state": 'rejected'
        }
        purchase_obj.write(vals)


