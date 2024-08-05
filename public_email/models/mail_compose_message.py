from odoo import models, fields, api, Command, _


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    email_to = fields.Char(
        'To', readonly=False, store=True, compute_sudo=False,
        help="Email address of the recipient.")

    @api.model
    def default_get(self, fields):
        res = super(MailComposeMessage, self).default_get(fields)
        if 'email_from' in fields:
            res['email_from'] = self.env.user.email_formatted
        return res

    def action_send_email(self):
        self.ensure_one()
        return self.with_context(email_to=self.email_to).action_send_mail()
