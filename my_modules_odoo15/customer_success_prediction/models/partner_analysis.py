import base64
import csv
import logging
from datetime import datetime
import matplotlib.pyplot as plt
from io import StringIO, BytesIO

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class PartnerDataAnalysis(models.Model):
    _name = 'partner.data.analysis'
    _description = 'Partner Data Analysis'

    name = fields.Char(compute='_compute_name', store=True)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)

    # Data file fields
    data_file = fields.Binary(string='Data File (CSV)', attachment=True)
    data_filename = fields.Char(string='Data Filename')

    # Analysis fields
    customer_since = fields.Float(
        string='Customer Since (years)',
        compute='_compute_statistics',
        store=True,
    )
    total_orders = fields.Integer(
        string='Total Orders',
        compute='_compute_statistics',
        store=True,
    )
    successful_orders_rate = fields.Float(
        string='Successful Orders Rate (%)',
        compute='_compute_statistics',
        store=True,
    )

    # Visualization fields
    amount_success_chart = fields.Binary(
        string='Success Rate by Order Amount',
        attachment=True
    )
    success_amount_chart = fields.Binary(
        string='Average Amount by Success Rate',
        attachment=True
    )

    @api.depends('partner_id')
    def _compute_name(self):
        for record in self:
            if record.partner_id:
                record.name = f"Analysis: {record.partner_id.name}"
            else:
                record.name = "New Analysis"

    def action_collect_data(self):
        """Collect data for selected partner and save to CSV"""
        self.ensure_one()

        if not self.partner_id:
            raise UserError(_('Please select a partner for analysis.'))

        # Collect data from database
        orders_data = self._collect_orders_data()
        if not orders_data:
            raise UserError(_('No orders found for the selected partner.'))

        # Prepare and save CSV data
        self._save_csv_data(orders_data)

        return True

    def _collect_orders_data(self):
        """Collect all necessary data from database"""
        self.ensure_one()

        # Get partner's orders
        orders = self.env['sale.order'].search([
            ('partner_id', '=', self.partner_id.id)
        ])

        if not orders:
            return []

        # Prepare data
        orders_data = []
        for order in orders:
            orders_data.append({
                'order_id': order.id,
                'date_order': order.date_order,
                'state': order.state,
                'amount_total': order.amount_total,
            })

        return orders_data

    def _save_csv_data(self, orders_data):
        """Save collected data to CSV file"""
        self.ensure_one()

        if not orders_data:
            return False

        # Prepare CSV data
        csv_data = [['order_id', 'date_order', 'state', 'amount_total']]
        for order in orders_data:
            csv_data.append([
                order['order_id'],
                order['date_order'],
                order['state'],
                order['amount_total']
            ])

        # Save to CSV
        csv_buffer = StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerows(csv_data)

        # Convert to base64 and save
        csv_content = csv_buffer.getvalue().encode()
        self.write({
            'data_file': base64.b64encode(csv_content),
            'data_filename': f'partner_analysis_{self.partner_id.id}_{self.partner_id.name}.csv',
        })

        return True

    def action_compute_statistics(self):
        self._compute_statistics()

    def _compute_statistics(self):
        for record in self:
            if not record.data_file:
                continue

            try:
                # Read CSV data
                csv_content = base64.b64decode(record.data_file).decode('utf-8')
                csv_file = StringIO(csv_content)
                reader = csv.DictReader(csv_file)
                data = list(reader)

                # Calculate customer since
                if data:
                    dates = [datetime.strptime(row['date_order'], '%Y-%m-%d %H:%M:%S') for row in data]
                    first_order_date = min(dates)
                    years_diff = (datetime.now() - first_order_date).days / 365.0
                    record.customer_since = round(years_diff, 2)
                else:
                    record.customer_since = 0

                # Calculate orders statistics
                record.total_orders = len(data)
                successful_orders = len([row for row in data if row['state'] == 'sale'])
                record.successful_orders_rate = (successful_orders / record.total_orders) if record.total_orders else 0

            except Exception as e:
                _logger.error(f"Error computing statistics: {str(e)}")
                record.customer_since = 0
                record.total_orders = 0
                record.successful_orders_rate = 0

    def action_visualize(self):
        """Create all visualization charts"""
        self.ensure_one()

        if not self.data_file:
            raise UserError(_('Please collect data first.'))

        try:
            # Create amount-success rate chart
            self.amount_success_chart = self._create_amount_success_chart(
                self._prepare_amount_success_data()
            )

            # Create success rate-amount chart
            self.success_amount_chart = self._create_success_amount_chart(
                self._prepare_success_amount_data()
            )

            return True

        except Exception as e:
            _logger.error(f"Error creating visualization: {str(e)}")
            raise UserError(_('Error creating visualization. Please check the logs.'))

    def _prepare_amount_success_data(self):
        """Prepare data for amount-success rate chart"""
        try:
            # Read CSV data
            csv_content = base64.b64decode(self.data_file).decode('utf-8')
            csv_file = StringIO(csv_content)
            reader = csv.DictReader(csv_file)
            data = list(reader)

            # Get amount range
            amounts = [float(row['amount_total']) for row in data]
            min_amount = min(amounts)
            max_amount = max(amounts)
            amount_range = max_amount - min_amount
            step = amount_range / 10

            # Group orders by amount ranges
            amount_groups = {i: {'total': 0, 'successful': 0}
                             for i in range(10)}

            for row in data:
                amount = float(row['amount_total'])
                group_index = min(int((amount - min_amount) / step), 9)
                amount_groups[group_index]['total'] += 1
                if row['state'] == 'sale':
                    amount_groups[group_index]['successful'] += 1

            # Calculate success rates
            result = {
                'ranges': [],
                'rates': [],
                'orders_count': []  # Додаємо список для кількості ордерів
            }

            for i in range(10):
                group = amount_groups[i]
                if group['total'] > 0:
                    rate = (group['successful'] / group['total']) * 100
                else:
                    rate = 0

                range_start = min_amount + (i * step)
                range_end = min_amount + ((i + 1) * step)
                result['ranges'].append(f'{range_start:.0f}-{range_end:.0f}')
                result['rates'].append(rate)
                result['orders_count'].append(group['total'])  # Додаємо кількість ордерів

            return result

        except Exception as e:
            _logger.error(f"Error preparing amount-success data: {str(e)}")
            return None

    def _create_amount_success_chart(self, data):
        """Create chart showing success rate by order amount"""
        if not data:
            return False

        try:
            plt.figure(figsize=(10, 6))

            # Фільтруємо точки з нульовою кількістю ордерів
            x_points = []
            y_points = []
            counts = []
            for i, (rate, count) in enumerate(zip(data['rates'], data['orders_count'])):
                if count > 0:
                    x_points.append(i)
                    y_points.append(rate)
                    counts.append(count)

            # Малюємо точки фіксованого розміру
            scatter = plt.scatter(x_points, y_points, s=100, alpha=0.6, c='blue')

            plt.title('Success Rate by Order Amount\n(numbers indicate order count)')
            plt.xlabel('Order Amount Range')
            plt.ylabel('Success Rate (%)')

            plt.xticks(range(len(data['ranges'])), data['ranges'],
                       rotation=45, ha='right')
            plt.grid(True, linestyle='--', alpha=0.7)

            # Додаємо числа біля точок під кутом 45 градусів
            for x, y, count in zip(x_points, y_points, counts):
                plt.annotate(str(count),
                             xy=(x, y),
                             xytext=(3, 3),  # Зміщення тексту вправо-вверх
                             textcoords='offset points',
                             ha='left',
                             va='bottom',
                             )

            # Save the plot
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight',
                        dpi=100, pad_inches=0.2)
            plt.close()

            return base64.b64encode(buffer.getvalue())

        except Exception as e:
            _logger.error(f"Error creating amount-success chart: {str(e)}")
            return False


    def _prepare_success_amount_data(self):
        """Prepare data for success rate-amount chart"""
        try:
            # Read CSV data
            csv_content = base64.b64decode(self.data_file).decode('utf-8')
            csv_file = StringIO(csv_content)
            reader = csv.DictReader(csv_file)
            data = list(reader)

            # Group orders by success rate ranges (0-10, 11-20, etc.)
            success_groups = {i: {'orders': [], 'total': 0, 'amount': 0}
                              for i in range(10)}

            # First pass: calculate success rate for each order
            partner_orders = {}
            for row in data:
                order_id = row['order_id']
                partner_orders[order_id] = {
                    'state': row['state'],
                    'amount': float(row['amount_total'])
                }

            # Calculate success rate and group orders
            total_orders = len(partner_orders)
            successful_orders = len([o for o in partner_orders.values()
                                     if o['state'] == 'sale'])
            success_rate = (successful_orders / total_orders * 100) if total_orders > 0 else 0

            # Group by success rate
            group_index = min(int(success_rate / 10), 9)
            for order_data in partner_orders.values():
                success_groups[group_index]['orders'].append(order_data['amount'])
                success_groups[group_index]['total'] += 1

            # Calculate average amount for each group
            result = {
                'ranges': [],
                'amounts': []
            }

            for i in range(10):
                group = success_groups[i]
                if group['orders']:
                    avg_amount = sum(group['orders']) / len(group['orders'])
                else:
                    avg_amount = 0

                result['ranges'].append(f'{i * 10}-{(i + 1) * 10}%')
                result['amounts'].append(avg_amount)

            return result

        except Exception as e:
            _logger.error(f"Error preparing success-amount data: {str(e)}")
            return None

    def _create_success_amount_chart(self, data):
        """Create chart showing average amount by success rate"""
        if not data:
            return False

        try:
            plt.figure(figsize=(10, 6))
            plt.bar(range(len(data['ranges'])), data['amounts'],
                    color='green', alpha=0.6)

            plt.title('Average Order Amount by Success Rate')
            plt.xlabel('Success Rate Range')
            plt.ylabel('Average Amount')

            plt.xticks(range(len(data['ranges'])), data['ranges'],
                       rotation=45, ha='right')
            plt.grid(True, linestyle='--', alpha=0.7)

            # Add value labels on top of bars
            for i, v in enumerate(data['amounts']):
                plt.text(i, v, f'{v:.0f}',
                         ha='center', va='bottom')

            # Save the plot
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight')
            plt.close()

            return base64.b64encode(buffer.getvalue())

        except Exception as e:
            _logger.error(f"Error creating success-amount chart: {str(e)}")
            return False
