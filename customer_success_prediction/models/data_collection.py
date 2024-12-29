import base64
import matplotlib
matplotlib.use('Agg')
from io import BytesIO
from datetime import datetime
import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np

from odoo import models, fields


class CustomerDataCollection(models.Model):
    _name = 'customer.data.collection'
    _description = 'Customer Data Collection'

    name = fields.Char(required=True)
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('collecting', 'Collecting'),
        ('done', 'Done')
    ], default='draft')

    # Загальна статистика
    total_partners = fields.Integer(string='Загальна кількість клієнтів', compute='_compute_statistics', store=True)
    total_orders = fields.Integer(string='Загальна кількість замовлень', compute='_compute_statistics', store=True)
    total_success_rate = fields.Float(string='Загальний % успішних замовлень', compute='_compute_statistics', store=True)

    # Розподіл по статусам
    orders_by_state = fields.Text(string='Розподіл замовлень по статусам', compute='_compute_statistics', store=True)
    orders_by_state_chart = fields.Binary(string='Orders by Status Distribution', compute='_compute_distribution_charts', store=True)

    # Розподіл клієнтів за success_rate
    partners_by_success_rate = fields.Text(string='Розподіл клієнтів за success_rate', compute='_compute_statistics', store=True)
    partners_by_rate_chart = fields.Binary(string='Partners by Success Rate Distribution', compute='_compute_distribution_charts', store=True)

    # Графіки
    combined_chart = fields.Binary(string='Monthly Orders Analysis', compute='_compute_charts')

    def _compute_statistics(self):
        for record in self:
            # Отримуємо всі замовлення за період
            domain = [
                ('date_order', '>=', record.date_from),
                ('date_order', '<=', record.date_to)
            ]
            orders = self.env['sale.order'].search(domain)
            partners = orders.mapped('partner_id')

            # Загальна статистика
            record.total_partners = len(partners)
            record.total_orders = len(orders)

            # Статистика по статусам
            states_count = defaultdict(int)
            for order in orders:
                states_count[order.state] += 1
            record.orders_by_state = str(dict(states_count))

            # Загальний % успішних замовлень
            successful_orders = orders.filtered(lambda o: o.state == 'sale')
            record.total_success_rate = (len(successful_orders) / len(orders)) if orders else 0

            # Розподіл клієнтів за success_rate
            success_rate_ranges = defaultdict(int)
            for partner in partners:
                partner_orders = orders.filtered(lambda o: o.partner_id == partner)
                partner_successful = partner_orders.filtered(lambda o: o.state == 'sale')
                success_rate = (len(partner_successful) / len(partner_orders) * 100) if partner_orders else 0

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

            record.partners_by_success_rate = str(dict(success_rate_ranges))

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

    def _compute_charts(self):
        for record in self:
            domain = [
                ('date_order', '>=', record.date_from),
                ('date_order', '<=', record.date_to)
            ]
            orders = self.env['sale.order'].search(domain)

            # Підготовка даних по місяцях
            monthly_data = defaultdict(lambda: {'orders': 0, 'successful': 0})

            for order in orders:
                month_key = order.date_order.strftime('%m/%Y')
                monthly_data[month_key]['orders'] += 1
                if order.state == 'sale':
                    monthly_data[month_key]['successful'] += 1

            # Сортуємо місяці
            months = sorted(monthly_data.keys(), key=lambda x: datetime.strptime(x, '%m/%Y'))

            # Prepare data arrays
            orders_data = [monthly_data[m]['orders'] for m in months]
            successful_data = [monthly_data[m]['successful'] for m in months]
            success_rate_data = [(monthly_data[m]['successful'] / monthly_data[m]['orders'] * 100)
                                 if monthly_data[m]['orders'] else 0 for m in months]

            # Create combined chart
            record.combined_chart = record._create_chart(
                months, orders_data, successful_data, success_rate_data)

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

    def _compute_distribution_charts(self):
        for record in self:
            try:
                # Get orders within date range
                domain = [
                    ('date_order', '>=', record.date_from),
                    ('date_order', '<=', record.date_to)
                ]
                orders = self.env['sale.order'].search(domain)
                partners = orders.mapped('partner_id')

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
                for order in orders:
                    states_count[order.state] += 1

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

                # Prepare partners by success rate data with ordered ranges and green shades
                success_ranges = [
                    ('0-20%', (0, 20)),
                    ('21-40%', (21, 40)),
                    ('41-60%', (41, 60)),
                    ('61-80%', (61, 80)),
                    ('81-100%', (81, 100))
                ]

                # Generate green shades from light to dark
                green_shades = [
                    '#c8e6c9',  # Very light green
                    '#a5d6a7',  # Light green
                    '#81c784',  # Medium green
                    '#66bb6a',  # Dark green
                    '#43a047'   # Very dark green
                ]

                partners_data = defaultdict(int)
                for partner in partners:
                    success_rate = partner.successful_order * 100
                    for range_name, (min_val, max_val) in success_ranges:
                        if min_val <= success_rate <= max_val:
                            partners_data[range_name] += 1
                            break

                # Create ordered dictionary
                ordered_partners_data = {range_name: partners_data.get(range_name, 0)
                                         for range_name, _ in success_ranges}

                # Create partners by success rate chart
                record.partners_by_rate_chart = record._create_distribution_chart(
                    ordered_partners_data,
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

    def action_collect_data(self):
        self.ensure_one()
        self.state = 'collecting'

        # Оновлюємо статистику
        self._compute_statistics()
        self._compute_charts()
        self._compute_distribution_charts()

        self.state = 'done'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Успіх',
                'message': f'Статистику зібрано для {self.total_partners} клієнтів та {self.total_orders} замовлень',
                'sticky': False,
                'type': 'success'
            }
        }
