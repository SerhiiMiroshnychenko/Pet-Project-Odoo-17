from odoo import api, models


class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.model_create_multi
    def create(self, values_list):
        context = self._context
        email_to = context.get('email_to')
        if email_to:
            for value in values_list:
                value['email_to'] = email_to
                value['recipient_ids'] = False
        return super(MailMail, self).create(values_list)
