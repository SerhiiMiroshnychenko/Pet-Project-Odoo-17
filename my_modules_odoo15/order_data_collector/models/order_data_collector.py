import csv
import base64
import logging
import pandas as pd
from io import StringIO

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class OrderDataCollector(models.Model):
    _name = 'order.data.collector'
    _description = 'Order Data Collector'

    name = fields.Char(required=True)
    prefix_number = fields.Integer(required=True)
    date_from = fields.Date(readonly=True)
    date_to = fields.Date(readonly=True)
    date_range_display = fields.Char(string='Analysis Period', compute='_compute_date_range_display', store=True)

    # Data file fields
    data_file = fields.Binary(string='Data File (CSV)', attachment=True)
    data_filename = fields.Char(string='Data Filename')

    # Statistics fields
    total_orders = fields.Integer(string='Total number of orders')
    successful_orders = fields.Integer(string='Number of successful orders')
    unsuccessful_orders = fields.Integer(string='Number of unsuccessful orders')
    total_partners = fields.Integer(string='Total number of unique clients')
    average_success_rate = fields.Float(string='Average order success rate', digits=(5, 2))
    average_amount = fields.Float(string='Average order amount', digits=(10, 2))
    average_messages = fields.Float(string='Average messages per order', digits=(10, 2))
    average_changes = fields.Float(string='Average changes per order', digits=(10, 2))
    average_order_amount = fields.Float(string='Average order amount', digits=(10, 2))
    average_order_messages = fields.Float(string='Average order messages', digits=(10, 2))
    average_order_changes = fields.Float(string='Average order changes', digits=(10, 2))
    partner_success_avg_amount = fields.Float(string='Partner success average amount', digits=(10, 2))
    partner_fail_avg_amount = fields.Float(string='Partner fail average amount', digits=(10, 2))
    partner_success_avg_messages = fields.Float(string='Partner success average messages', digits=(10, 2))
    partner_fail_avg_messages = fields.Float(string='Partner fail average messages', digits=(10, 2))
    partner_success_avg_changes = fields.Float(string='Partner success average changes', digits=(10, 2))
    partner_fail_avg_changes = fields.Float(string='Partner fail average changes', digits=(10, 2))

    @api.depends('date_from', 'date_to')
    def _compute_date_range_display(self):
        """Compute display string for date range"""
        for record in self:
            if record.date_from and record.date_to:
                # Calculate the difference in days
                delta = (record.date_to - record.date_from).days

                # Convert to years and months
                years = delta // 365
                remaining_days = delta % 365
                months = remaining_days // 30

                # Build the display string
                parts = []
                if years > 0:
                    parts.append(f"{years} {'year' if years == 1 else 'years'}")
                if months > 0:
                    parts.append(f"{months} {'month' if months == 1 else 'months'}")

                record.date_range_display = f"{' '.join(parts)} (from {record.date_from.strftime('%d.%m.%Y')} to {record.date_to.strftime('%d.%m.%Y')})"
            else:
                record.date_range_display = "Period not defined"

    def action_collect_data(self):
        """Collect all necessary data and save to CSV"""
        self.ensure_one()
        try:
            # SQL query to get order data with success rates
            query = """
                WITH order_data AS (
                    SELECT 
                        so.id as order_id,
                        so.name as order_name,
                        so.create_date as create_date,
                        so.partner_id,
                        so.state,
                        so.amount_total as order_amount,
                        CASE WHEN so.state = 'sale' THEN 1 ELSE 0 END as is_successful,
                        (
                            SELECT COUNT(DISTINCT m.id)
                            FROM mail_message m 
                            WHERE m.res_id = so.id AND m.model = 'sale.order'
                        ) as order_messages,
                        (
                            SELECT COUNT(DISTINCT CASE 
                                WHEN EXISTS (
                                    SELECT 1 FROM mail_tracking_value mtv 
                                    WHERE mtv.mail_message_id = m.id
                                ) THEN m.id 
                            END)
                            FROM mail_message m
                            WHERE m.res_id = so.id AND m.model = 'sale.order'
                        ) as order_changes,
                        (
                            SELECT COALESCE(
                                CAST(COUNT(CASE WHEN s2.state = 'sale' THEN 1 END) AS DECIMAL(10,2)) /
                                NULLIF(COUNT(*), 0),
                                0
                            )
                            FROM sale_order s2
                            WHERE s2.partner_id = so.partner_id
                            AND s2.create_date < so.create_date
                        ) as partner_success_rate,
                        (
                            SELECT COUNT(*)
                            FROM sale_order s2
                            WHERE s2.partner_id = so.partner_id
                            AND s2.create_date < so.create_date
                        ) as partner_total_orders,
                        (
                            SELECT 
                                EXTRACT(DAY FROM (so.create_date - MIN(s2.create_date)))::INTEGER
                            FROM sale_order s2
                            WHERE s2.partner_id = so.partner_id
                            AND s2.create_date < so.create_date
                        ) as partner_order_age_days,
                        (
                            SELECT COALESCE(AVG(s2.amount_total), 0)
                            FROM sale_order s2
                            WHERE s2.partner_id = so.partner_id
                            AND s2.create_date < so.create_date
                        ) as partner_avg_amount,
                        (
                            SELECT COALESCE(AVG(s2.amount_total), 0)
                            FROM sale_order s2
                            WHERE s2.partner_id = so.partner_id
                            AND s2.create_date < so.create_date
                            AND s2.state = 'sale'
                        ) as partner_success_avg_amount,
                        (
                            SELECT COALESCE(AVG(s2.amount_total), 0)
                            FROM sale_order s2
                            WHERE s2.partner_id = so.partner_id
                            AND s2.create_date < so.create_date
                            AND s2.state != 'sale'
                        ) as partner_fail_avg_amount,
                        (
                            SELECT COUNT(DISTINCT m.id)
                            FROM sale_order s2
                            LEFT JOIN mail_message m ON m.res_id = s2.id AND m.model = 'sale.order'
                            WHERE s2.partner_id = so.partner_id
                            AND s2.create_date < so.create_date
                        ) as partner_total_messages,
                        (
                            SELECT COALESCE(AVG(message_count), 0)
                            FROM (
                                SELECT s2.id, COUNT(DISTINCT m.id) as message_count
                                FROM sale_order s2
                                LEFT JOIN mail_message m ON m.res_id = s2.id AND m.model = 'sale.order'
                                WHERE s2.partner_id = so.partner_id
                                AND s2.create_date < so.create_date
                                AND s2.state = 'sale'
                                GROUP BY s2.id
                            ) as t
                        ) as partner_success_avg_messages,
                        (
                            SELECT COALESCE(AVG(message_count), 0)
                            FROM (
                                SELECT s2.id, COUNT(DISTINCT m.id) as message_count
                                FROM sale_order s2
                                LEFT JOIN mail_message m ON m.res_id = s2.id AND m.model = 'sale.order'
                                WHERE s2.partner_id = so.partner_id
                                AND s2.create_date < so.create_date
                                AND s2.state != 'sale'
                                GROUP BY s2.id
                            ) as t
                        ) as partner_fail_avg_messages,
                        (
                            SELECT COALESCE(
                                CAST(COUNT(DISTINCT CASE 
                                    WHEN EXISTS (
                                        SELECT 1 FROM mail_tracking_value mtv 
                                        WHERE mtv.mail_message_id = m2.id
                                    ) THEN m2.id 
                                END) AS DECIMAL(10,2)) /
                                NULLIF(COUNT(DISTINCT s2.id), 0),
                                0
                            )
                            FROM sale_order s2
                            LEFT JOIN mail_message m2 ON m2.res_id = s2.id AND m2.model = 'sale.order'
                            WHERE s2.partner_id = so.partner_id
                            AND s2.create_date < so.create_date
                        ) as partner_avg_changes,
                        (
                            SELECT COALESCE(AVG(change_count), 0)
                            FROM (
                                SELECT s2.id,
                                COUNT(DISTINCT CASE 
                                    WHEN EXISTS (
                                        SELECT 1 FROM mail_tracking_value mtv 
                                        WHERE mtv.mail_message_id = m2.id
                                    ) THEN m2.id 
                                END) as change_count
                                FROM sale_order s2
                                LEFT JOIN mail_message m2 ON m2.res_id = s2.id AND m2.model = 'sale.order'
                                WHERE s2.partner_id = so.partner_id
                                AND s2.create_date < so.create_date
                                AND s2.state = 'sale'
                                GROUP BY s2.id
                            ) as t
                        ) as partner_success_avg_changes,
                        (
                            SELECT COALESCE(AVG(change_count), 0)
                            FROM (
                                SELECT s2.id,
                                COUNT(DISTINCT CASE 
                                    WHEN EXISTS (
                                        SELECT 1 FROM mail_tracking_value mtv 
                                        WHERE mtv.mail_message_id = m2.id
                                    ) THEN m2.id 
                                END) as change_count
                                FROM sale_order s2
                                LEFT JOIN mail_message m2 ON m2.res_id = s2.id AND m2.model = 'sale.order'
                                WHERE s2.partner_id = so.partner_id
                                AND s2.create_date < so.create_date
                                AND s2.state != 'sale'
                                GROUP BY s2.id
                            ) as t
                        ) as partner_fail_avg_changes
                    FROM sale_order so
                    ORDER BY so.create_date
                )
                SELECT
                    %s * 1000000 + order_id as order_id_with_prefix,
                    order_name,
                    is_successful,
                    create_date,
                    %s * 1000000 + partner_id as partner_id_with_prefix,
                    order_amount,
                    order_messages,
                    order_changes,
                    COALESCE(partner_success_rate * 100, 0) as partner_success_rate,
                    COALESCE(partner_total_orders, 0) as partner_total_orders,
                    COALESCE(partner_order_age_days, 0) as partner_order_age_days,
                    COALESCE(partner_avg_amount, 0) as partner_avg_amount,
                    COALESCE(partner_success_avg_amount, 0) as partner_success_avg_amount,
                    COALESCE(partner_fail_avg_amount, 0) as partner_fail_avg_amount,
                    COALESCE(partner_total_messages, 0) as partner_total_messages,
                    COALESCE(partner_success_avg_messages, 0) as partner_success_avg_messages,
                    COALESCE(partner_fail_avg_messages, 0) as partner_fail_avg_messages,
                    COALESCE(partner_avg_changes, 0) as partner_avg_changes,
                    COALESCE(partner_success_avg_changes, 0) as partner_success_avg_changes,
                    COALESCE(partner_fail_avg_changes, 0) as partner_fail_avg_changes
                FROM order_data
            """

            self.env.cr.execute(query, (self.prefix_number, self.prefix_number))
            results = self.env.cr.fetchall()

            if not results:
                raise UserError(_("No data found to analyze"))

            # Prepare CSV data
            output = StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow(['order_id', 'order_name', 'is_successful', 'create_date', 'partner_id',
                             'order_amount', 'order_messages', 'order_changes',
                             'partner_success_rate', 'partner_total_orders', 'partner_order_age_days',
                             'partner_avg_amount', 'partner_success_avg_amount', 'partner_fail_avg_amount',
                             'partner_total_messages', 'partner_success_avg_messages', 'partner_fail_avg_messages',
                             'partner_avg_changes', 'partner_success_avg_changes', 'partner_fail_avg_changes'])

            # Write data rows
            for row in results:
                writer.writerow(row)

            # Save dates
            self.date_from = min(row[3] for row in results)
            self.date_to = max(row[3] for row in results)

            # Save CSV file
            encoded_data = base64.b64encode(output.getvalue().encode())
            self.write({
                'data_file': encoded_data,
                'data_filename': f"{self.env.cr.dbname}_{self.prefix_number}.csv"
            })

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Data collected successfully'),
                    'sticky': False,
                    'type': 'success',
                }
            }

        except Exception as e:
            _logger.error("Error while collecting data: %s", str(e))
            raise UserError(_("Error while collecting data: %s") % str(e))

    def action_compute_statistics(self):
        """Compute basic statistics from the collected data"""
        self.ensure_one()
        try:
            if not self.data_file:
                raise UserError(_("No data file found. Please collect data first."))

            # Read CSV data
            csv_data = StringIO(base64.b64decode(self.data_file).decode())
            df = pd.read_csv(csv_data)

            print('\n')
            print('*'*30)
            # Set display options for all columns
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            print("DataFrame columns:", df.columns.tolist())
            print("\nFirst few rows of DataFrame:")
            print(df.head())
            print('*'*30)
            print('\n')

            # Calculate statistics
            self.total_orders = len(df)
            self.successful_orders = df['is_successful'].sum()
            self.unsuccessful_orders = self.total_orders - self.successful_orders
            self.total_partners = df['partner_id'].nunique()
            self.average_success_rate = (self.successful_orders / self.total_orders) if self.total_orders else 0
            self.average_amount = df['partner_avg_amount'].mean()
            self.average_messages = df['partner_total_messages'].mean()
            self.average_changes = df['partner_avg_changes'].mean()
            self.average_order_amount = df['order_amount'].mean()
            self.average_order_messages = df['order_messages'].mean()
            self.average_order_changes = df['order_changes'].mean()
            self.partner_success_avg_amount = df['partner_success_avg_amount'].mean()
            self.partner_fail_avg_amount = df['partner_fail_avg_amount'].mean()
            self.partner_success_avg_messages = df['partner_success_avg_messages'].mean()
            self.partner_fail_avg_messages = df['partner_fail_avg_messages'].mean()
            self.partner_success_avg_changes = df['partner_success_avg_changes'].mean()
            self.partner_fail_avg_changes = df['partner_fail_avg_changes'].mean()

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Statistics computed successfully'),
                    'sticky': False,
                    'type': 'success',
                }
            }

        except Exception as e:
            _logger.error("Error computing statistics: %s", str(e))
            raise UserError(_("Error computing statistics: %s") % str(e))
