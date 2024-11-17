import re
import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = "res.partner"

    html_content = fields.Html(
        compute='_compute_html_content',
        sanitize=False,
        sanitize_tags=False,
        sanitize_attributes=False)

    def _compute_html_content(self):
        for partner in self:
            fields_info = []
            # Get all fields of the model
            sorted_fields = sorted(partner._fields.items(), key=lambda item: item[0])
            for field_name, field in sorted_fields:
                value = partner[field_name]
                # Convert value to string representation
                if isinstance(value, models.BaseModel):
                    value = value.mapped('display_name')
                fields_info.append(f"<i>{field_name}</i>: <b>{value}</b>")
            info_data = '<br/>'.join(fields_info)
            
            # Create HTML content with Information button
            html_content = f"""
            <sheet>{info_data}</sheet>
            """
            
            partner.html_content = html_content

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
