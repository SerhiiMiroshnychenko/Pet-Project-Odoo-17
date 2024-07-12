import re
import logging

from odoo import models, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = "res.partner"

    @api.constrains('email')
    def email_address_validate(self):
        """
        Regular expression Email Address validation
        """

        email_validate_pattern = re.compile(
            r'^(?![.-])'  # Local part should not start with a dot or hyphen
            r'^(?!.*\.\.)'  # Prevent consecutive dots in any part
            r'[a-zA-Z0-9._%+-]+'  # Local part can include alphanumeric characters and special characters . _ % + -
            r'(?<![._%+-])'  # Local part should not end with characters [._%+-]
            r'@[a-zA-Z0-9-]+'  # Domain part have to start with @ and can include alphanumeric characters and hyphens
            r'(?:\.[a-zA-Z0-9-]+)*'  # Allow subdomains with the same rules as the domain part
            r'\.[a-zA-Z]{2,}$'  # Top-level domain (e.g., .com, .org) - should start with a dot followed by at least
            # two alphabetic characters
        )
        for rec in self:
            try:
                is_valid = email_validate_pattern.match(rec.email)
            except Exception as e:
                _logger.error(str(e))
                is_valid = False
            if not is_valid:
                raise ValidationError(_(f'`{rec.email}` is NOT a valid email address.'))
