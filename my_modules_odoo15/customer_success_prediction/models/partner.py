import base64
import logging
import matplotlib
import numpy as np
matplotlib.use('Agg')  # Install backend before importing pyplot
from io import BytesIO
from datetime import datetime
import matplotlib.pyplot as plt
from collections import defaultdict

from odoo import models, fields, api, Command

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit='res.partner'

    # Analytics fields
    successful_order = fields.Float(compute='_compute_orders_statistics')
    orders_chart_bar = fields.Binary(
        string='Orders Chart (Bar)',
        compute='_compute_charts',
        help='Bar chart showing orders statistics by month'
    )
    orders_chart_line = fields.Binary(
        string='Orders Chart (Line)',
        compute='_compute_charts',
        help='Line chart showing orders statistics by month'
    )
    success_avg_chart = fields.Binary(
        string='Success/Average Chart',
        compute='_compute_charts',
        help='Line chart showing success rate and average amount'
    )
    success_total_chart = fields.Binary(
        string='Success/Total Chart',
        compute='_compute_charts',
        help='Line chart showing success rate and total amount'
    )
    total_orders_amount = fields.Float(
        string='Total Orders Amount',
        compute='_compute_orders_statistics',
        help='Total amount of all orders'
    )
    successful_orders_amount = fields.Float(
        string='Successful Orders Amount',
        compute='_compute_orders_statistics',
        help='Total amount of successful orders'
    )
    failed_orders_amount = fields.Float(
        string='Failed Orders Amount',
        compute='_compute_orders_statistics',
        help='Total amount of failed orders'
    )
    average_order_amount = fields.Float(
        string='Average Order Amount',
        compute='_compute_orders_statistics',
        help='Average amount per order'
    )
    average_successful_amount = fields.Float(
        string='Average Successful Amount',
        compute='_compute_orders_statistics',
        help='Average amount per successful order'
    )
    average_failed_amount = fields.Float(
        string='Average Failed Amount',
        compute='_compute_orders_statistics',
        help='Average amount per failed order'
    )
    all_order_ids = fields.Many2many('sale.order', compute='_compute_all_orders')
    customer_since = fields.Float(
        string='Клієнт вже (років)',
        compute='_compute_customer_since',
        store=True,
        help='Кількість років, протягом яких контакт є клієнтом'
    )

    def update_analytics(self):
        self._compute_orders_statistics()
        self._compute_charts()

    def _compute_all_orders(self):
        for partner in self:
            domain = partner.action_view_sale_order().get('domain')
            if domain:
                orders = self.env['sale.order'].search(domain)
            else:
                orders = partner.sale_order_ids
            partner.update({
                'all_order_ids': [Command.set(orders.ids)]
            })

    @api.depends('sale_order_ids', 'sale_order_ids.state')
    def _compute_orders_statistics(self):
        for partner in self:
            orders = partner.all_order_ids
            completed_orders = orders.filtered(lambda o: o.state == 'sale')
            partner.successful_order = (len(completed_orders) / len(orders)) if orders else 0
            partner.total_orders_amount = sum(order.amount_total for order in orders)
            partner.successful_orders_amount = sum(order.amount_total for order in completed_orders)
            partner.failed_orders_amount = partner.total_orders_amount - partner.successful_orders_amount
            partner.average_order_amount = partner.total_orders_amount / len(orders) if orders else 0
            partner.average_successful_amount = partner.successful_orders_amount / len(completed_orders) if completed_orders else 0
            partner.average_failed_amount = partner.failed_orders_amount / (len(orders) - len(completed_orders)) if (len(orders) - len(completed_orders)) else 0

    @api.depends('sale_order_ids', 'sale_order_ids.date_order')
    def _compute_customer_since(self):
        for partner in self:
            if not partner.sale_order_ids:
                partner.customer_since = 0
                continue

            # Знаходимо дату першого замовлення
            first_order_date = min(
                order.date_order for order in partner.sale_order_ids if order.date_order
            )

            if not first_order_date:
                partner.customer_since = 0
                continue

            # Обчислюємо різницю в роках
            delta = datetime.now() - first_order_date
            partner.customer_since = round(delta.days / 365.25, 2)  # враховуємо високосні роки

    def _compute_charts(self):
        _logger.info("Starting _compute_charts")
        for partner in self:
            try:
                _logger.info(f"Processing partner {partner.id}")
                # Get orders data
                orders = partner.all_order_ids.filtered(lambda o: o.date_order)
                _logger.info(f"Found {len(orders)} orders with dates")

                if not orders:
                    partner.orders_chart_bar = False
                    partner.orders_chart_line = False
                    partner.success_avg_chart = False
                    partner.success_total_chart = False
                    continue

                # Prepare data by month
                monthly_data = defaultdict(lambda: {'total': 0, 'completed': 0, 'rate': 0, 'amount': 0.0, 'completed_amount': 0.0})

                for order in orders:
                    month_key = order.date_order.strftime('%m/%Y')
                    monthly_data[month_key]['total'] += 1
                    monthly_data[month_key]['amount'] += order.amount_total
                    if order.state == 'sale':
                        monthly_data[month_key]['completed'] += 1
                        monthly_data[month_key]['completed_amount'] += order.amount_total

                _logger.info(f"Processed data by months: {dict(monthly_data)}")

                # Calculate success rate and average amount for each month
                for month, data in monthly_data.items():
                    data['rate'] = (data['completed'] / data['total'] * 100) if data['total'] > 0 else 0
                    data['avg_amount'] = data['amount'] / data['total'] if data['total'] > 0 else 0

                # Sort months chronologically
                months = sorted(monthly_data.keys(),
                                key=lambda x: datetime.strptime(x, '%m/%Y'))

                # Prepare data arrays
                orders_data = [monthly_data[m]['total'] for m in months]
                completed_data = [monthly_data[m]['completed'] for m in months]
                rate_data = [monthly_data[m]['rate'] for m in months]
                avg_amount_data = [monthly_data[m]['avg_amount'] for m in months]
                total_amount_data = [monthly_data[m]['amount'] for m in months]

                _logger.info(f"Prepared data arrays: months={months}, orders={orders_data}, completed={completed_data}, rate={rate_data}")

                # Create bar chart
                bar_chart = self._create_bar_chart(months, orders_data, completed_data, rate_data)
                if bar_chart:
                    partner.orders_chart_bar = bar_chart
                    _logger.info("Bar chart created successfully")
                else:
                    _logger.error("Failed to create bar chart")

                # Create line chart
                line_chart = self._create_line_chart(months, orders_data, completed_data, rate_data)
                if line_chart:
                    partner.orders_chart_line = line_chart
                    _logger.info("Line chart created successfully")
                else:
                    _logger.error("Failed to create line chart")

                # Create success/average chart
                success_avg_chart = self._create_success_avg_chart(months, rate_data, avg_amount_data)
                if success_avg_chart:
                    partner.success_avg_chart = success_avg_chart
                    _logger.info("Success/average chart created successfully")
                else:
                    _logger.error("Failed to create success/average chart")

                # Create success/total chart
                success_total_chart = self._create_success_total_chart(months, rate_data, total_amount_data)
                if success_total_chart:
                    partner.success_total_chart = success_total_chart
                    _logger.info("Success/total chart created successfully")
                else:
                    _logger.error("Failed to create success/total chart")

            except Exception as e:
                _logger.error(f"Error computing charts for partner {partner.id}: {str(e)}")
                partner.orders_chart_bar = False
                partner.orders_chart_line = False
                partner.success_avg_chart = False
                partner.success_total_chart = False

    @staticmethod
    def _create_bar_chart(months, orders_data, successful_data, rate_data):
        """Create bar chart with three metrics"""
        try:
            plt.close('all')  # Close any existing plots

            # Create figure with primary axis
            fig, ax1 = plt.subplots(figsize=(12, 7))

            # Create second axis that shares x with ax1
            ax2 = ax1.twinx()

            # Set bar width
            bar_width = 0.35

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

            plt.title('Customer Orders Analysis')

            # Set x-axis labels
            ax1.set_xticks(x)
            ax1.set_xticklabels(months, rotation=45, ha='right')

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
            _logger.warning(f"Error creating chart: {str(e)}")
            return False
        finally:
            plt.close('all')

    @staticmethod
    def _create_line_chart(months, orders_data, successful_data, rate_data):
        """Create line chart with three metrics"""
        try:
            plt.close('all')  # Close any existing plots

            # Create figure and axis objects with larger size
            fig, ax1 = plt.subplots(figsize=(12, 7))
            ax2 = ax1.twinx()

            # Create lines
            x = np.arange(len(months))
            line1 = ax1.plot(x, orders_data, color='#2196F3', label='Total Orders', marker='o')
            line2 = ax1.plot(x, successful_data, color='#4CAF50', label='Successful Orders', marker='s')
            line3 = ax2.plot(x, rate_data, color='#FFC107', label='Success Rate (%)', marker='^')

            # Customize axes
            ax1.set_xlabel('Month')
            ax1.set_ylabel('Number of Orders')
            ax2.set_ylabel('Success Rate (%)')

            # Set x-axis ticks
            ax1.set_xticks(x)
            ax1.set_xticklabels(months, rotation=45, ha='right')

            # Add grid
            ax1.grid(True, linestyle='--', alpha=0.7)

            # Add legends
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

            # Adjust layout with more bottom margin
            plt.subplots_adjust(bottom=0.2)

            # Convert plot to base64 image
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            plt.close('all')

            return base64.b64encode(buffer.getvalue())

        except Exception as e:
            _logger.error(f"Error creating line chart: {str(e)}")
            return False
        finally:
            plt.close('all')

    @staticmethod
    def _create_success_avg_chart(months, rate_data, avg_data):
        """Create line chart with success rate and average amount"""
        try:
            plt.close('all')  # Close any existing plots

            # Create figure and axis objects with larger size
            fig, ax1 = plt.subplots(figsize=(12, 7))
            ax2 = ax1.twinx()

            # Create lines
            x = np.arange(len(months))
            line1 = ax1.plot(x, rate_data, color='#2196F3', label='Success Rate (%)', marker='o')
            line2 = ax2.plot(x, avg_data, color='#4CAF50', label='Average Amount', marker='s')

            # Customize axes
            ax1.set_xlabel('Month')
            ax1.set_ylabel('Success Rate (%)')
            ax2.set_ylabel('Average Amount')

            # Set x-axis ticks
            ax1.set_xticks(x)
            ax1.set_xticklabels(months, rotation=45, ha='right')

            # Add grid
            ax1.grid(True, linestyle='--', alpha=0.7)

            # Add legends
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

            # Adjust layout with more bottom margin
            plt.subplots_adjust(bottom=0.2)

            # Convert plot to base64 image
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            plt.close('all')

            return base64.b64encode(buffer.getvalue())

        except Exception as e:
            _logger.error(f"Error creating success/average chart: {str(e)}")
            return False
        finally:
            plt.close('all')

    @staticmethod
    def _create_success_total_chart(months, rate_data, total_data):
        """Create line chart with success rate and total amount"""
        try:
            plt.close('all')  # Close any existing plots

            # Create figure and axis objects with larger size
            fig, ax1 = plt.subplots(figsize=(12, 7))
            ax2 = ax1.twinx()

            # Create lines
            x = np.arange(len(months))
            line1 = ax1.plot(x, rate_data, color='#2196F3', label='Success Rate (%)', marker='o')
            line2 = ax2.plot(x, total_data, color='#4CAF50', label='Total Amount', marker='s')

            # Customize axes
            ax1.set_xlabel('Month')
            ax1.set_ylabel('Success Rate (%)')
            ax2.set_ylabel('Total Amount')

            # Set x-axis ticks
            ax1.set_xticks(x)
            ax1.set_xticklabels(months, rotation=45, ha='right')

            # Add grid
            ax1.grid(True, linestyle='--', alpha=0.7)

            # Add legends
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

            # Adjust layout with more bottom margin
            plt.subplots_adjust(bottom=0.2)

            # Convert plot to base64 image
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            plt.close('all')

            return base64.b64encode(buffer.getvalue())

        except Exception as e:
            _logger.error(f"Error creating success/total chart: {str(e)}")
            return False
        finally:
            plt.close('all')
