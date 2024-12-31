import base64
import csv
import logging
import matplotlib
matplotlib.use('Agg')
from io import BytesIO, StringIO
from datetime import datetime
import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class CustomerDataCollection(models.Model):
    _name = 'customer.data.collection'
    _description = 'Customer Data Collection'

    name = fields.Char(required=True)
    date_from = fields.Date()
    date_to = fields.Date()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('data_collected', 'Data Collected'),
        ('charts_created', 'Charts Created')
    ], default='draft')

    # Data file fields
    data_file = fields.Binary(string='Data File (CSV)', attachment=True)
    data_filename = fields.Char(string='Data Filename')

    # Statistics fields (computed from CSV data)
    total_partners = fields.Integer(string='Загальна кількість клієнтів', compute='_compute_statistics', store=True, depends=['data_file', 'state'])
    total_orders = fields.Integer(string='Загальна кількість замовлень', compute='_compute_statistics', store=True, depends=['data_file', 'state'])
    total_success_rate = fields.Float(string='Загальний % успішних замовлень', compute='_compute_statistics', store=True, depends=['data_file', 'state'])

    # Distribution fields
    orders_by_state = fields.Text(string='Розподіл замовлень по статусам', compute='_compute_statistics', store=True, depends=['data_file', 'state'])
    orders_by_state_chart = fields.Binary(string='Orders by Status Distribution', compute='_compute_distribution_charts', store=True, depends=['data_file', 'state'])
    partners_by_success_rate = fields.Text(string='Розподіл клієнтів за success_rate', compute='_compute_statistics', store=True, depends=['data_file', 'state'])
    partners_by_rate_chart = fields.Binary(string='Partners by Success Rate Distribution', compute='_compute_distribution_charts', store=True, depends=['data_file', 'state'])
    combined_chart = fields.Binary(string='Monthly Orders Analysis', compute='_compute_charts', depends=['data_file', 'state'])

    def action_collect_data(self):
        """Collect data from database and save to CSV"""
        self.ensure_one()

        # Validate dates when collecting data
        if not self.date_from or not self.date_to:
            raise UserError(_('Please specify date range for data collection.'))

        if self.date_from > self.date_to:
            raise UserError(_('Start date must be before end date.'))

        # Get orders within date range
        domain = [
            ('date_order', '>=', self.date_from),
            ('date_order', '<=', self.date_to)
        ]
        orders = self.env['sale.order'].search(domain)

        if not orders:
            raise UserError(_('No orders found in the specified date range.'))

        # Prepare CSV data
        csv_data = self._prepare_csv_data(orders)

        # Save to CSV
        csv_buffer = StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerows(csv_data)

        # Convert to base64
        csv_content = csv_buffer.getvalue().encode()
        self.write({
            'data_file': base64.b64encode(csv_content),
            'data_filename': f'customer_data_{self.date_from}_{self.date_to}.csv',
            'state': 'data_collected'
        })

        return True

    def _prepare_csv_data(self, orders):
        """Prepare raw data for CSV file"""
        # Header
        csv_data = [['order_id', 'partner_id', 'date_order', 'state', 'amount_total']]

        # Data rows
        for order in orders:
            csv_data.append([
                order.id,
                order.partner_id.id,
                order.date_order,
                order.state,
                order.amount_total
            ])

        return csv_data

    def _validate_csv_data(self, csv_content):
        """Validate CSV file structure and content"""
        try:
            csv_file = StringIO(csv_content.decode())
            reader = csv.reader(csv_file)
            header = next(reader)

            required_columns = ['order_id', 'partner_id', 'date_order', 'state', 'amount_total']
            if not all(col in header for col in required_columns):
                raise UserError(_('Invalid CSV format. Required columns: %s') % ', '.join(required_columns))

            return True
        except Exception as e:
            raise UserError(_('Error validating CSV file: %s') % str(e))

    def _read_csv_data(self):
        _logger.info("Starting _read_csv_data")
        if not self.data_file:
            _logger.warning("No data file found")
            return []

        try:
            # Decode base64 data
            csv_data = base64.b64decode(self.data_file).decode('utf-8')
            _logger.info("Successfully decoded CSV data")

            # Read CSV data
            csv_file = StringIO(csv_data)
            reader = csv.DictReader(csv_file)
            data = []

            for row in reader:
                # Convert date strings to datetime objects
                if 'date_order' in row and row['date_order']:
                    try:
                        row['date_order'] = datetime.strptime(row['date_order'], '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        _logger.warning(f"Invalid date format in row: {row}")
                        continue

                # Ensure required fields are present
                if 'partner_id' not in row or 'state' not in row:
                    _logger.warning(f"Missing required fields in row: {row}")
                    continue

                data.append(row)

            _logger.info(f"Successfully read {len(data)} rows from CSV")
            return data

        except Exception as e:
            _logger.error(f"Error reading CSV data: {str(e)}")
            return []

    def action_create_charts(self):
        """Create charts from CSV data"""
        self.ensure_one()

        if not self.data_file:
            raise UserError(_('Please collect data or upload a CSV file first.'))

        try:
            # Read CSV data
            data = self._read_csv_data()
            if not data:
                raise UserError(_('No data available in the CSV file.'))

            # Update state to trigger chart creation
            self.write({'state': 'charts_created'})

            return True
        except Exception as e:
            raise UserError(_('Error creating charts: %s') % str(e))

    @api.depends('data_file', 'state')
    def _compute_statistics(self):
        _logger.info("Starting _compute_statistics")
        for record in self:
            _logger.info(f"Processing record {record.id}, state: {record.state}")
            if record.state == 'draft':
                # Reset all statistics in draft state
                record.total_partners = 0
                record.total_orders = 0
                record.total_success_rate = 0
                record.orders_by_state = '{}'
                record.partners_by_success_rate = '{}'
                _logger.info(f"Reset statistics for record {record.id} in draft state")
                continue

            # Read CSV data
            data = record._read_csv_data()
            _logger.info(f"Read {len(data)} rows from CSV for record {record.id}")
            if not data:
                continue

            # Initialize statistics
            partners = set()  # використовуємо set для унікальних партнерів
            total_orders = 0
            successful_orders = 0
            orders_by_state = defaultdict(int)
            partners_success_rate = defaultdict(lambda: {'total': 0, 'successful': 0})

            # Process data
            for row in data:
                partner_id = int(row['partner_id'])
                order_state = row['state']

                # Update statistics
                partners.add(partner_id)
                total_orders += 1
                orders_by_state[order_state] += 1

                # Update partner success rate
                partners_success_rate[partner_id]['total'] += 1
                if order_state == 'sale':
                    partners_success_rate[partner_id]['successful'] += 1
                    successful_orders += 1

            _logger.info(f"Processed data for record {record.id}: {len(partners)} partners, {total_orders} orders")

            # Calculate success rate ranges
            success_rate_ranges = defaultdict(int)
            for partner_data in partners_success_rate.values():
                success_rate = (partner_data['successful'] / partner_data['total'] * 100) if partner_data['total'] > 0 else 0

                # Розподіляємо по діапазонах
                if success_rate == 100:
                    range_key = '100%'
                elif success_rate >= 80:
                    range_key = '80-99%'
                elif success_rate >= 60:
                    range_key = '60-79%'
                elif success_rate >= 40:
                    range_key = '40-59%'
                elif success_rate >= 20:
                    range_key = '20-39%'
                else:
                    range_key = '0-19%'

                success_rate_ranges[range_key] += 1

            # Update computed fields
            record.total_partners = len(partners)
            record.total_orders = total_orders
            record.total_success_rate = (successful_orders / total_orders * 100) if total_orders > 0 else 0
            record.orders_by_state = str(dict(orders_by_state))
            record.partners_by_success_rate = str(dict(success_rate_ranges))

            _logger.info(f"Updated statistics for record {record.id}")

    @api.depends('data_file', 'state')
    def _compute_distribution_charts(self):
        _logger.info("Starting _compute_distribution_charts")
        for record in self:
            if record.state == 'draft' or not record.data_file:
                record.orders_by_state_chart = False
                record.partners_by_rate_chart = False
                continue

            try:
                # Read CSV data
                data = record._read_csv_data()
                if not data:
                    continue

                # Prepare orders by state data with specific order and colors
                state_order = ['draft', 'sent', 'sale', 'cancel']
                state_colors = {
                    'draft': '#808080',  # Gray
                    'sent': '#FFD700',   # Yellow
                    'sale': '#28a745',   # Green
                    'cancel': '#dc3545'  # Red
                }

                # Count orders by state
                states_count = defaultdict(int)
                for row in data:
                    states_count[row['state']] += 1

                # Create ordered dictionary with all states (even if count is 0)
                states_data = {state: states_count.get(state, 0) for state in state_order}
                state_colors_list = [state_colors[state] for state in state_order]

                # Create orders by state chart
                record.orders_by_state_chart = record._create_distribution_chart(
                    states_data,
                    'Orders Distribution by Status',
                    'Status',
                    'Number of Orders',
                    state_colors_list
                )

                # Prepare partners by success rate data
                partners_data = defaultdict(lambda: {'total': 0, 'successful': 0})
                for row in data:
                    partner_id = int(row['partner_id'])
                    partners_data[partner_id]['total'] += 1
                    if row['state'] == 'sale':
                        partners_data[partner_id]['successful'] += 1

                # Calculate success rates and group by ranges
                success_ranges = [
                    ('0-19%', (0, 19)),
                    ('20-39%', (20, 39)),
                    ('40-59%', (40, 59)),
                    ('60-79%', (60, 79)),
                    ('80-99%', (80, 99)),
                    ('100%', (100, 100))
                ]

                success_rate_ranges = defaultdict(int)
                for partner_stats in partners_data.values():
                    success_rate = (partner_stats['successful'] / partner_stats['total'] * 100) if partner_stats['total'] > 0 else 0
                    for range_name, (min_val, max_val) in success_ranges:
                        if min_val <= success_rate <= max_val:
                            success_rate_ranges[range_name] += 1
                            break

                # Generate green shades from light to dark
                green_shades = [
                    '#c8e6c9',  # Very light green
                    '#a5d6a7',  # Light green
                    '#81c784',  # Medium green
                    '#66bb6a',  # Dark green
                    '#43a047',  # Very dark green
                    '#2e7d32'   # Extra dark green
                ]

                # Create ordered dictionary for success rate ranges
                ordered_success_data = {range_name: success_rate_ranges.get(range_name, 0)
                                        for range_name, _ in success_ranges}

                # Create partners by success rate chart
                record.partners_by_rate_chart = record._create_distribution_chart(
                    ordered_success_data,
                    'Partners Distribution by Success Rate',
                    'Success Rate Range',
                    'Number of Partners',
                    green_shades
                )

            except Exception as e:
                print(f"Error computing distribution charts: {str(e)}")
                record.orders_by_state_chart = False
                record.partners_by_rate_chart = False
            finally:
                plt.close('all')

    def _compute_charts(self):
        for record in self:
            if record.state == 'draft' or not record.data_file:
                record.combined_chart = False
                continue

            # Read CSV data
            data = record._read_csv_data()
            if not data:
                continue

            # Initialize data arrays
            monthly_data = defaultdict(lambda: {'orders': 0, 'successful': 0, 'rate': 0})

            # Process data
            for row in data:
                if not row['date_order']:
                    continue

                month_key = row['date_order'].strftime('%m/%Y')
                monthly_data[month_key]['orders'] += 1
                if row['state'] == 'sale':
                    monthly_data[month_key]['successful'] += 1

            # Calculate success rate for each month
            for month_data in monthly_data.values():
                month_data['rate'] = (month_data['successful'] / month_data['orders'] * 100) if month_data['orders'] > 0 else 0

            # Sort months chronologically
            sorted_months = sorted(monthly_data.keys(),
                                   key=lambda x: datetime.strptime(x, '%m/%Y'))

            # Create data arrays in chronological order
            months = sorted_months
            orders_data = [monthly_data[month]['orders'] for month in months]
            successful_data = [monthly_data[month]['successful'] for month in months]
            rate_data = [monthly_data[month]['rate'] for month in months]

            if not months:
                record.combined_chart = False
                continue

            # Create combined chart
            record.combined_chart = record._create_chart(
                months, orders_data, successful_data, rate_data)

    @staticmethod
    def _create_chart(months, orders_data, successful_data, rate_data):
        """Helper function for creating combined chart with three metrics"""
        try:
            # Create figure with primary axis
            fig, ax1 = plt.subplots(figsize=(15, 8))

            # Create second axis that shares x with ax1
            ax2 = ax1.twinx()

            # Set the positions for the bars
            x = np.arange(len(months))
            width = 0.25  # width of the bars

            # Plot bars
            bars1 = ax1.bar(x - width, orders_data, width, label='Total Orders', color='skyblue')
            bars2 = ax1.bar(x, successful_data, width, label='Successful Orders', color='green')
            bars3 = ax2.bar(x + width, rate_data, width, label='Success Rate (%)', color='orange')

            # Set labels and title
            ax1.set_xlabel('Month')
            ax1.set_ylabel('Number of Orders')
            ax2.set_ylabel('Success Rate (%)')

            plt.title('Monthly Orders Analysis')

            # Set x-axis labels
            months_display = [datetime.strptime(m, '%m/%Y').strftime('%B %Y') for m in months]
            plt.xticks(x, months_display, rotation=45, ha='right')

            # Add grid
            ax1.grid(True, axis='y', linestyle='--', alpha=0.7)

            # Add values above bars
            def autolabel(bars, ax):
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                            f'{int(height)}',
                            ha='center', va='bottom')

            autolabel(bars1, ax1)
            autolabel(bars2, ax1)
            autolabel(bars3, ax2)

            # Add legends
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

            # Adjust layout
            plt.tight_layout()

            # Save to buffer
            buffer = BytesIO()
            fig.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
            plt.close()

            return base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error creating chart: {str(e)}")
            return False
        finally:
            plt.close('all')

    @staticmethod
    def _create_distribution_chart(data, title, xlabel, ylabel, colors):
        """Helper function for creating distribution charts"""
        try:
            # Create figure
            fig, ax = plt.subplots(figsize=(12, 6))

            # Get data
            labels = list(data.keys())
            values = list(data.values())

            # Create bars with specific colors
            x = np.arange(len(labels))
            bars = ax.bar(x, values, color=colors)

            # Customize chart
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
            ax.set_title(title)

            # Set x-axis labels
            ax.set_xticks(x)
            ax.set_xticklabels(labels, rotation=45, ha='right')

            # Add grid
            ax.grid(True, axis='y', linestyle='--', alpha=0.7)

            # Add values above bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}',
                        ha='center', va='bottom')

            # Adjust layout
            plt.tight_layout()

            # Save to buffer
            buffer = BytesIO()
            fig.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
            plt.close()

            return base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error creating distribution chart: {str(e)}")
            return False
        finally:
            plt.close('all')
