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
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CustomerDataCollection(models.Model):
    _name = 'customer.data.collection'
    _description = 'Customer Data Collection'

    name = fields.Char(required=True)
    date_from = fields.Date(readonly=True)
    date_to = fields.Date(readonly=True)
    date_range_display = fields.Char(string='Analysis Period', compute='_compute_date_range_display', store=True)

    # Data file fields
    data_file = fields.Binary(string='Data File (CSV)', attachment=True)
    data_filename = fields.Char(string='Data Filename')

    # Statistics fields (computed from CSV data)
    total_partners = fields.Integer(string='Total number of clients', compute='_compute_statistics', store=True)
    total_orders = fields.Integer(string='Total number of orders', compute='_compute_statistics', store=True)
    total_success_rate = fields.Float(string='Total % of successful orders', compute='_compute_statistics', store=True)

    # Distribution fields
    orders_by_state = fields.Text(string='Distribution of orders by status', compute='_compute_statistics', store=True)
    orders_by_state_chart = fields.Binary(string='Orders by Status Distribution',
                                          compute='_compute_distribution_charts', store=True)
    partners_by_success_rate = fields.Text(string='Distribution of customers by success_rate',
                                           compute='_compute_statistics', store=True)
    partners_by_rate_chart = fields.Binary(string='Partners by Success Rate Distribution',
                                           compute='_compute_distribution_charts', store=True)
    partners_by_rate_plot = fields.Binary(string='Partners Success Rate Plot', compute='_compute_distribution_charts',
                                          store=True)
    monthly_analysis_chart = fields.Binary(string='Monthly Orders Analysis', compute='_compute_monthly_charts')

    # Amount-Success Rate Analysis
    amount_success_chart = fields.Binary(
        string='Success Rate by Order Amount',
        attachment=True
    )
    partner_age_success_chart = fields.Binary(
        string='Success Rate by Partner Age',
        attachment=True
    )
    salesperson_success_chart = fields.Binary(
        string='Success Rate by Salesperson',
        compute='_compute_distribution_charts',
        store=True
    )
    weekday_success_chart = fields.Binary(
        string='Success Rate by Weekday',
        compute='_compute_weekday_charts',
        store=True
    )
    month_success_chart = fields.Binary(
        string='Success Rate by Month',
        compute='_compute_month_charts',
        store=True
    )
    partner_orders_success_chart = fields.Binary(
        string='Success Rate by Partner Orders Count',
        compute='_compute_partner_orders_charts',
        store=True
    )
    total_amount_success_chart = fields.Binary(
        string='Success Rate by Total Orders Amount',
        compute='_compute_amount_success_charts',
        store=True
    )
    success_amount_success_chart = fields.Binary(
        string='Success Rate by Successful Orders Amount',
        compute='_compute_amount_success_charts',
        store=True
    )
    avg_amount_success_chart = fields.Binary(
        string='Success Rate by Average Order Amount',
        compute='_compute_amount_success_charts',
        store=True
    )
    avg_success_amount_success_chart = fields.Binary(
        string='Success Rate by Average Successful Order Amount',
        compute='_compute_amount_success_charts',
        store=True
    )
    cumulative_success_rate_chart = fields.Binary(
        string='Cumulative Success Rate Over Time',
        compute='_compute_cumulative_success_rate_chart',
        store=True
    )
    order_intensity_success_chart = fields.Binary(
        string='Success Rate by Total Order Intensity',
        compute='_compute_order_intensity_chart',
        store=True
    )
    success_order_intensity_chart = fields.Binary(
        string='Success Rate by Successful Order Intensity',
        compute='_compute_success_order_intensity_chart',
        store=True
    )
    amount_intensity_success_chart = fields.Binary(
        string='Success Rate by Total Amount Intensity',
        compute='_compute_amount_intensity_chart',
        store=True
    )
    success_amount_intensity_chart = fields.Binary(
        string='Success Rate by Successful Amount Intensity',
        compute='_compute_success_amount_intensity_chart',
        store=True
    )
    monthly_success_rate_chart = fields.Binary(
        string='Monthly Success Rate',
        compute='_compute_monthly_success_rate_chart',
        store=True
    )
    monthly_volume_success_chart = fields.Binary(
        string='Success Rate by Monthly Order Volume',
        compute='_compute_monthly_volume_success_chart',
        store=True
    )
    monthly_orders_success_chart = fields.Binary(
        string='Success Rate by Monthly Orders Count',
        compute='_compute_monthly_orders_success_chart',
        store=True
    )
    payment_term_success_chart = fields.Binary(
        string='Success Rate by Payment Terms',
        compute='_compute_payment_term_success_chart',
        store=True
    )

    cumulative_monthly_analysis_chart = fields.Binary(
        string='Cumulative Monthly Analysis',
        compute='_compute_cumulative_monthly_charts',
        store=True
    )

    monthly_analysis_scatter_chart = fields.Binary(
        string='Monthly Analysis (Scatter)',
        compute='_compute_monthly_scatter_charts',
        store=True
    )

    monthly_combined_chart = fields.Binary(
        string='Monthly Combined Analysis',
        compute='_compute_monthly_combined_chart',
        store=True
    )

    relative_age_success_chart = fields.Binary(
        string='Success Rate by Relative Customer Age',
        compute='_compute_relative_age_success_chart',
        store=True
    )

    # SALESPERSON ANALYSIS

    salesperson_age_success_chart = fields.Binary(
        string='Success Rate by Salesperson Age',
        compute='_compute_salesperson_age_success_chart',
        store=True
    )

    salesperson_orders_success_chart = fields.Binary(
        string='Success Rate by Salesperson Orders Count',
        compute='_compute_salesperson_orders_success_chart',
        store=True
    )

    salesperson_total_amount_success_chart = fields.Binary(
        string='Success Rate by Salesperson Total Amount',
        compute='_compute_salesperson_total_amount_success_chart',
        store=True
    )

    salesperson_success_amount_success_chart = fields.Binary(
        string='Success Rate by Salesperson Successful Orders Amount',
        compute='_compute_salesperson_success_amount_success_chart',
        store=True
    )

    salesperson_avg_amount_success_chart = fields.Binary(
        string='Success Rate by Average Order Amount per Salesperson',
        compute='_compute_salesperson_avg_amount_success_chart',
        store=True
    )

    salesperson_avg_success_amount_success_chart = fields.Binary(
        string='Success Rate by Average Successful Order Amount per Salesperson',
        compute='_compute_salesperson_avg_success_amount_success_chart',
        store=True
    )

    salesperson_order_intensity_success_chart = fields.Binary(
        string='Success Rate by Total Order Intensity per Salesperson',
        compute='_compute_salesperson_order_intensity_chart',
        store=True
    )

    salesperson_success_order_intensity_chart = fields.Binary(
        string='Success Rate by Successful Order Intensity per Salesperson',
        compute='_compute_salesperson_success_order_intensity_chart',
        store=True
    )

    salesperson_amount_intensity_success_chart = fields.Binary(
        string='Success Rate by Total Amount Intensity per Salesperson',
        compute='_compute_salesperson_amount_intensity_chart',
        store=True
    )

    salesperson_success_amount_intensity_chart = fields.Binary(
        string='Success Rate by Successful Amount Intensity per Salesperson',
        compute='_compute_salesperson_success_amount_intensity_chart',
        store=True
    )



    def action_collect_data(self):
        """Collect data from database and save to CSV"""
        self.ensure_one()

        try:
            # Get sale orders
            orders = self.env['sale.order'].search([])
            print(f"\nFound {len(orders)} orders")
            partners = self.env['res.partner'].search([])
            print(f"\nFound {len(partners)} partners")

            # Prepare CSV data
            csv_data = self._prepare_csv_data(orders)
            print(f"Prepared {len(csv_data)} rows of data")

            # Convert to CSV
            output = StringIO()
            writer = csv.writer(output)
            writer.writerows(csv_data)

            # Save to binary field
            self.data_file = base64.b64encode(output.getvalue().encode('utf-8'))
            self.data_filename = f'customer_data_{fields.Date.today()}.csv'

            return True

        except Exception as e:
            raise UserError(_('Error collecting data: %s') % str(e))

    def _prepare_csv_data(self, orders):
        """Prepare raw data for CSV file"""
        print("\nPreparing CSV data...")

        # Find min and max dates
        min_date = False
        max_date = False
        for order in orders:
            order_date = order.date_order.date()
            if not min_date or order_date < min_date:
                min_date = order_date
            if not max_date or order_date > max_date:
                max_date = order_date

        # Update date range
        self.date_from = min_date
        self.date_to = max_date

        # Header
        csv_data = [['order_id', 'partner_id', 'date_order', 'state', 'amount_total',
                     'partner_create_date', 'user_id', 'payment_term_id']]

        # Data rows
        for order in orders:
            csv_data.append([
                order.id,
                order.partner_id.id,
                order.date_order,
                order.state,
                order.amount_total,
                order.partner_id.create_date,
                order.user_id.id if order.user_id else False,
                order.payment_term_id.id if order.payment_term_id else False
            ])

        print(f"CSV data prepared. Total rows: {len(csv_data)}")
        return csv_data

    def action_compute_statistics(self):
        if not self.data_file:
            raise UserError(_('Please collect data or upload a CSV file first.'))
        self._compute_statistics()

    def _validate_csv_data(self, csv_content):
        """Validate CSV file structure and content"""
        try:
            csv_file = StringIO(csv_content.decode())
            reader = csv.reader(csv_file)
            header = next(reader)

            required_columns = ['order_id', 'partner_id', 'date_order', 'state', 'amount_total',
                                'partner_create_date', 'user_id', 'payment_term_id']
            if not all(col in header for col in required_columns):
                raise UserError(_('Invalid CSV format. Required columns: %s') % ', '.join(required_columns))

            return True
        except Exception as e:
            raise UserError(_('Error validating CSV file: %s') % str(e))

    def _read_csv_data(self):
        print("Starting _read_csv_data")
        if not self.data_file:
            print("No data file found")
            return []

        try:
            # Decode base64 data
            csv_data = base64.b64decode(self.data_file).decode('utf-8')
            print("Successfully decoded CSV data")

            # Read CSV data
            csv_file = StringIO(csv_data)
            reader = csv.DictReader(csv_file)
            data = []
            for row in reader:
                try:
                    # Обрізаємо мікросекунди з дат
                    if 'date_order' in row:
                        date_str = row['date_order'].split('.')[0]  # Видаляємо мікросекунди
                        row['date_order'] = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    continue

                try:
                    if 'partner_create_date' in row:
                        date_str = row['partner_create_date'].split('.')[0]  # Видаляємо мікросекунди
                        row['partner_create_date'] = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    continue

                # Ensure required fields are present
                if not all(field in row for field in
                           ['order_id', 'partner_id', 'date_order', 'state', 'amount_total',
                            'partner_create_date', 'user_id', 'payment_term_id']):
                    print(f"Missing required fields in row: {row}")
                    continue

                data.append(row)

            print(f"Successfully read {len(data)} rows from CSV")
            return data

        except Exception as e:
            print(f"Error reading CSV data: {str(e)}")
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

            self._compute_charts()

            return True
        except Exception as e:
            raise UserError(_('Error creating charts: %s') % str(e))

    def action_visualize(self):
        """Create all visualization charts"""
        self.ensure_one()
        print("\n=== Starting action_visualize ===")

        if not self.data_file:
            raise UserError(_('Please collect data first.'))

        try:
            # Create amount-success rate chart
            print("\n--- Preparing amount-success data ---")
            amount_success_data = self._prepare_amount_success_data()
            if amount_success_data:
                print("Creating amount-success chart")
                self.amount_success_chart = self._create_amount_success_chart(amount_success_data)
            else:
                print("WARNING: No amount-success data available")

            # Create partner age-success rate chart
            print("\n--- Preparing partner-age success data ---")
            partner_age_success_data = self._prepare_partner_age_success_data()
            if partner_age_success_data:
                print("Creating partner-age success chart")
                self.partner_age_success_chart = self._create_partner_age_success_chart(partner_age_success_data)
            else:
                print("WARNING: No partner-age success data available")

            self._compute_month_charts()
            self._compute_weekday_charts()
            self._compute_partner_orders_charts()
            self._compute_amount_success_charts()
            self._compute_cumulative_success_rate_chart()
            self._compute_order_intensity_chart()
            self._compute_success_order_intensity_chart()
            self._compute_amount_intensity_chart()
            self._compute_success_amount_intensity_chart()
            self._compute_monthly_success_rate_chart()
            self._compute_monthly_volume_success_chart()
            self._compute_monthly_orders_success_chart()
            self._compute_payment_term_success_chart()

            return True

        except Exception as e:
            print(f"\nERROR in action_visualize: {str(e)}")
            import traceback
            print(traceback.format_exc())
            raise UserError(_('Error creating visualization. Please check the logs.'))

    def _prepare_amount_success_data(self):
        """Prepare data for amount-success rate chart"""
        try:
            # Read CSV data
            data = self._read_csv_data()
            if not data:
                return None

            # Get all amounts and sort them
            amounts_data = [(float(row['amount_total']), row['state'] == 'sale')
                            for row in data]

            # Видаляємо замовлення з нульовою сумою
            amounts_data = [x for x in amounts_data if x[0] > 0]
            amounts_data.sort(key=lambda x: x[0])

            total_orders = len(amounts_data)
            if total_orders == 0:
                return None

            # Визначаємо кількість груп (зменшуємо якщо замовлень мало)
            num_groups = min(30, total_orders // 50)  # Мінімум 50 замовлень на групу
            if num_groups < 5:  # Якщо груп менше 5, встановлюємо мінімум 5 груп
                num_groups = 5

            # Розраховуємо розмір кожної групи
            group_size = total_orders // num_groups
            remainder = total_orders % num_groups

            # Ініціалізуємо результат
            result = {
                'ranges': [],
                'rates': [],
                'orders_count': []
            }

            # Розбиваємо на групи
            start_idx = 0
            for i in range(num_groups):
                # Додаємо +1 до розміру групи для перших remainder груп
                current_group_size = group_size + (1 if i < remainder else 0)
                if current_group_size == 0:
                    break

                end_idx = start_idx + current_group_size
                group_orders = amounts_data[start_idx:end_idx]

                # Рахуємо статистику для групи
                min_amount = group_orders[0][0]
                max_amount = group_orders[-1][0]
                successful = sum(1 for _, is_success in group_orders if is_success)
                success_rate = (successful / len(group_orders)) * 100

                # Форматуємо діапазон в залежності від розміру чисел
                if max_amount >= 1000000:  # Більше 1 млн
                    range_str = f'{min_amount / 1000000:.1f}M-{max_amount / 1000000:.1f}M'
                elif max_amount >= 1000:  # Більше 1000
                    range_str = f'{min_amount / 1000:.0f}K-{max_amount / 1000:.0f}K'
                else:
                    range_str = f'{min_amount:.0f}-{max_amount:.0f}'

                # Додаємо дані до результату
                result['ranges'].append(range_str)
                result['rates'].append(success_rate)
                result['orders_count'].append(len(group_orders))

                start_idx = end_idx

            return result

        except Exception as e:
            print(f"Error preparing amount-success data: {str(e)}")
            return None

    def _create_amount_success_chart(self, data):
        """Create chart showing success rate by order amount"""
        if not data:
            return False

        try:
            plt.figure(figsize=(15, 8))

            # Фільтруємо точки з нульовою кількістю ордерів
            x_points = []
            y_points = []
            counts = []
            for i, (rate, count) in enumerate(zip(data['rates'], data['orders_count'])):
                if count > 0:
                    x_points.append(i)
                    y_points.append(rate)
                    counts.append(count)

            # Створюємо градієнт кольорів від червоного до зеленого в залежності від success rate
            colors = ['#ff4d4d' if rate < 50 else '#00cc00' for rate in y_points]
            sizes = [max(80, min(150, count / 2)) for count in counts]  # Розмір точки залежить від кількості замовлень

            # Малюємо точки
            scatter = plt.scatter(x_points, y_points, s=sizes, alpha=0.6, c=colors)

            # Розраховуємо середню кількість ордерів на точку
            avg_orders = sum(counts) // len(counts) if counts else 0

            plt.title(
                f'Success Rate by Order Amount\n(each point represents ~{avg_orders} orders, point size shows relative number in range)',
                pad=20, fontsize=12)
            plt.xlabel('Order Amount Range', fontsize=10)
            plt.ylabel('Success Rate (%)', fontsize=10)

            # Налаштовуємо осі
            plt.ylim(-5, 105)  # Додаємо трохи простору зверху і знизу

            # Показуємо всі мітки, якщо їх менше 10, інакше кожну другу
            if len(data['ranges']) <= 10:
                plt.xticks(range(len(data['ranges'])), data['ranges'],
                           rotation=45, ha='right')
            else:
                plt.xticks(range(len(data['ranges']))[::2],
                           [data['ranges'][i] for i in range(0, len(data['ranges']), 2)],
                           rotation=45, ha='right')

            plt.grid(True, linestyle='--', alpha=0.7)

            # Додаємо горизонтальні лінії
            plt.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
            plt.axhline(y=50, color='gray', linestyle='--', alpha=0.3)
            plt.axhline(y=100, color='gray', linestyle='-', alpha=0.3)

            # Додаємо легенду
            legend_elements = [
                plt.Line2D([0], [0], marker='o', color='w',
                           markerfacecolor='#ff4d4d', markersize=10,
                           label='Success Rate < 50%'),
                plt.Line2D([0], [0], marker='o', color='w',
                           markerfacecolor='#00cc00', markersize=10,
                           label='Success Rate ≥ 50%')
            ]
            plt.legend(handles=legend_elements, loc='upper right')

            # Зберігаємо графік
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight',
                        dpi=100, pad_inches=0.2)
            plt.close()

            return base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error creating amount-success chart: {str(e)}")
            return False

    def _prepare_partner_age_success_data(self):
        """Prepare data for partner age-success rate chart"""
        try:
            print("\nStarting _prepare_partner_age_success_data")

            # Read CSV data
            data = self._read_csv_data()
            if not data:
                print("WARNING: No CSV data available")
                return None

            # Розраховуємо вік партнера для кожного замовлення
            partner_age_data = []
            print("\nProcessing partner age data...")

            missing_create_date = 0
            missing_order_date = 0
            processed_rows = 0
            error_rows = 0

            for row in data:
                if not row.get('partner_create_date'):
                    missing_create_date += 1
                    continue
                if not row.get('date_order'):
                    missing_order_date += 1
                    continue

                try:
                    # Якщо дати в строковому форматі, конвертуємо їх
                    if isinstance(row['partner_create_date'], str):
                        row['partner_create_date'] = datetime.strptime(row['partner_create_date'], '%Y-%m-%d %H:%M:%S')
                    if isinstance(row['date_order'], str):
                        row['date_order'] = datetime.strptime(row['date_order'], '%Y-%m-%d %H:%M:%S')

                    partner_age = (row['date_order'] - row['partner_create_date']).days
                    partner_age_data.append((partner_age, row['state'] == 'sale'))
                    processed_rows += 1
                except Exception as e:
                    error_rows += 1

            print(f"\nProcessing summary:")
            print(f"- Total rows: {len(data)}")
            print(f"- Missing create date: {missing_create_date}")
            print(f"- Missing order date: {missing_order_date}")
            print(f"- Successfully processed: {processed_rows}")
            print(f"- Errors: {error_rows}")

            if not partner_age_data:
                print("WARNING: No valid partner age data found")
                return None

            print(f"Found {len(partner_age_data)} valid orders for analysis")
            # Сортуємо за віком партнера
            partner_age_data.sort(key=lambda x: x[0])

            total_orders = len(partner_age_data)
            print(f"Total orders for analysis: {total_orders}")

            # Визначаємо кількість груп
            num_groups = min(30, total_orders // 50)
            if num_groups < 5:
                num_groups = 5
            print(f"Number of groups: {num_groups}")

            # Розраховуємо розмір кожної групи
            group_size = total_orders // num_groups
            remainder = total_orders % num_groups
            print(f"Group size: {group_size}, remainder: {remainder}")

            # Ініціалізуємо результат
            result = {
                'ranges': [],
                'rates': [],
                'orders_count': []
            }

            # Розбиваємо на групи
            start_idx = 0
            for i in range(num_groups):
                current_group_size = group_size + (1 if i < remainder else 0)
                if current_group_size == 0:
                    break

                end_idx = start_idx + current_group_size
                group_orders = partner_age_data[start_idx:end_idx]

                # Рахуємо статистику для групи
                min_age = group_orders[0][0]
                max_age = group_orders[-1][0]
                successful = sum(1 for _, is_success in group_orders if is_success)
                success_rate = (successful / len(group_orders)) * 100

                print(f"\nGroup {i}:")
                print(f"- Orders: {len(group_orders)}")
                print(f"- Success rate: {success_rate:.1f}%")
                print(f"- Age range: {min_age}-{max_age} days")

                # Форматуємо діапазон
                if max_age >= 365:
                    range_str = f'{min_age / 365:.1f}y-{max_age / 365:.1f}y'
                elif max_age >= 30:
                    range_str = f'{min_age / 30:.0f}m-{max_age / 30:.0f}m'
                else:
                    range_str = f'{min_age}d-{max_age}d'

                # Додаємо дані до результату
                result['ranges'].append(range_str)
                result['rates'].append(success_rate)
                result['orders_count'].append(len(group_orders))

                start_idx = end_idx

            print("\nSuccessfully prepared partner age success data")
            return result

        except Exception as e:
            print(f"\nERROR in _prepare_partner_age_success_data: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return None

    def _create_partner_age_success_chart(self, data):
        """Create chart showing success rate by partner age"""
        if not data:
            return False

        try:
            plt.figure(figsize=(15, 8))

            # Фільтруємо точки з нульовою кількістю ордерів
            x_points = []
            y_points = []
            counts = []
            for i, (rate, count) in enumerate(zip(data['rates'], data['orders_count'])):
                if count > 0:
                    x_points.append(i)
                    y_points.append(rate)
                    counts.append(count)

            # Створюємо градієнт кольорів від червоного до зеленого в залежності від success rate
            colors = ['#ff4d4d' if rate < 50 else '#00cc00' for rate in y_points]
            sizes = [max(80, min(150, count / 2)) for count in counts]  # Розмір точки залежить від кількості замовлень

            # Малюємо точки
            scatter = plt.scatter(x_points, y_points, s=sizes, alpha=0.6, c=colors)

            # Розраховуємо середню кількість ордерів на точку
            avg_orders = sum(counts) // len(counts) if counts else 0

            plt.title(
                f'Success Rate by Partner Age\n(each point represents ~{avg_orders} orders, point size shows relative number in range)',
                pad=20, fontsize=12)
            plt.xlabel('Partner Age (d=days, m=months, y=years)', fontsize=10)
            plt.ylabel('Success Rate (%)', fontsize=10)

            # Налаштовуємо осі
            plt.ylim(-5, 105)

            # Показуємо всі мітки, якщо їх менше 10, інакше кожну другу
            if len(data['ranges']) <= 10:
                plt.xticks(range(len(data['ranges'])), data['ranges'],
                           rotation=45, ha='right')
            else:
                plt.xticks(range(len(data['ranges']))[::2],
                           [data['ranges'][i] for i in range(0, len(data['ranges']), 2)],
                           rotation=45, ha='right')

            plt.grid(True, linestyle='--', alpha=0.7)

            # Додаємо горизонтальні лінії
            plt.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
            plt.axhline(y=50, color='gray', linestyle='--', alpha=0.3)
            plt.axhline(y=100, color='gray', linestyle='-', alpha=0.3)

            # Додаємо легенду
            legend_elements = [
                plt.Line2D([0], [0], marker='o', color='w',
                           markerfacecolor='#ff4d4d', markersize=10,
                           label='Success Rate < 50%'),
                plt.Line2D([0], [0], marker='o', color='w',
                           markerfacecolor='#00cc00', markersize=10,
                           label='Success Rate ≥ 50%')
            ]
            plt.legend(handles=legend_elements, loc='upper right')

            # Зберігаємо графік
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight',
                        dpi=100, pad_inches=0.2)
            plt.close()

            return base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error creating partner-age success chart: {str(e)}")
            return False

    def _compute_statistics(self):
        print("Starting _compute_statistics")
        for record in self:
            print(f"Processing record {record.id}")

            # Read CSV data
            data = record._read_csv_data()
            print(f"Read {len(data)} rows from CSV for record {record.id}")
            if not data:
                continue

            # Initialize statistics
            partners = set()  # використовуємо set для унікальних партнерів
            total_orders = 0
            successful_orders = 0
            orders_by_state = defaultdict(int)
            partners_success_rate = defaultdict(lambda: {'total': 0, 'successful': 0})
            salesperson_success_rate = defaultdict(lambda: {'total': 0, 'successful': 0})

            # Process data
            for row in data:
                partner_id = int(row['partner_id'])
                order_state = row['state']
                user_id = row['user_id']

                # Update statistics
                partners.add(partner_id)
                total_orders += 1
                orders_by_state[order_state] += 1

                # Update partner success rate
                partners_success_rate[partner_id]['total'] += 1
                if order_state == 'sale':
                    partners_success_rate[partner_id]['successful'] += 1
                    successful_orders += 1

                # Update salesperson success rate
                if user_id:
                    salesperson_success_rate[user_id]['total'] += 1
                    if order_state == 'sale':
                        salesperson_success_rate[user_id]['successful'] += 1

            print(f"Processed data for record {record.id}: {len(partners)} partners, {total_orders} orders")

            # Calculate success rate ranges
            success_rate_ranges = defaultdict(int)
            for partner_data in partners_success_rate.values():
                success_rate = (partner_data['successful'] / partner_data['total'] * 100) if partner_data[
                                                                                                 'total'] > 0 else 0

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
            record.total_success_rate = (successful_orders / total_orders) if total_orders > 0 else 0
            record.orders_by_state = str(dict(orders_by_state))
            record.partners_by_success_rate = str(dict(success_rate_ranges))

            # Create salesperson success rate chart
            salesperson_success_data = []
            for user_id, data in salesperson_success_rate.items():
                success_rate = (data['successful'] / data['total'] * 100) if data['total'] > 0 else 0
                salesperson_success_data.append((user_id, success_rate))

            salesperson_success_data.sort(key=lambda x: x[1])
            record.salesperson_success_chart = record._create_salesperson_success_chart(salesperson_success_data)

            print(f"Updated statistics for record {record.id}")

    def _compute_charts(self):
        self._compute_distribution_charts()
        self._compute_monthly_charts()
        self._compute_cumulative_monthly_charts()
        self._compute_monthly_scatter_charts()

    def _compute_distribution_charts(self):
        """Compute distribution charts"""
        print("\nStarting _compute_distribution_charts")
        for record in self:
            if not record.data_file:
                record.orders_by_state_chart = False
                record.partners_by_rate_chart = False
                record.partners_by_rate_plot = False
                record.salesperson_success_chart = False
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
                    'sent': '#FFD700',  # Yellow
                    'sale': '#28a745',  # Green
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

                # Calculate success rates per partner
                partner_orders = defaultdict(list)
                for row in data:
                    partner_orders[row['partner_id']].append(row['state'])

                partner_success_rates = {}
                for partner_id, states in partner_orders.items():
                    success_count = states.count('sale')
                    total_count = len(states)
                    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
                    partner_success_rates[partner_id] = success_rate

                # Create partners rate charts
                record.partners_by_rate_chart = record._create_partners_rate_chart(partner_success_rates)
                record.partners_by_rate_plot = record._create_partners_rate_plot(partner_success_rates)

                # Create salesperson success rate chart
                print("\nPreparing salesperson data...")
                salesperson_orders = defaultdict(lambda: {'total': 0, 'successful': 0})

                # Збираємо статистику
                for row in data:
                    if row['user_id']:
                        salesperson_orders[row['user_id']]['total'] += 1
                        if row['state'] == 'sale':
                            salesperson_orders[row['user_id']]['successful'] += 1

                print(f"\nFound {len(salesperson_orders)} salespersons")

                # Формуємо дані для графіка
                salesperson_success_data = []
                for user_id, stats in salesperson_orders.items():
                    success_rate = (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0
                    salesperson_success_data.append({
                        'user_id': user_id,
                        'success_rate': success_rate,
                        'total_orders': stats['total']
                    })

                # Сортуємо за success_rate
                salesperson_success_data.sort(key=lambda x: x['success_rate'])

                print("\nFirst 3 records of prepared data:")
                for i, item in enumerate(salesperson_success_data[:3]):
                    print(f"Record {i + 1}:")
                    print(f"  user_id: {item['user_id']}")
                    print(f"  success_rate: {item['success_rate']:.2f}%")
                    print(f"  total_orders: {item['total_orders']}")

                # Створюємо графік
                record.salesperson_success_chart = record._create_salesperson_success_chart(salesperson_success_data)

            except Exception as e:
                print(f"Error computing distribution charts: {str(e)}")
                import traceback
                print(traceback.format_exc())
                record.orders_by_state_chart = False
                record.partners_by_rate_chart = False
                record.partners_by_rate_plot = False
                record.salesperson_success_chart = False
            finally:
                plt.close('all')

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
                days = remaining_days % 30

                # Build the display string
                parts = []
                if years > 0:
                    parts.append(f"{years} {'year' if years == 1 else 'years'}")
                if months > 0:
                    parts.append(f"{months} {'month' if months == 1 else 'months'}")
                if days > 0 and not years:  # show days only if period is less than a year
                    parts.append(f"{days} {'day' if days == 1 else 'days'}")

                record.date_range_display = f"{' '.join(parts)} (from {record.date_from.strftime('%d.%m.%Y')} to {record.date_to.strftime('%d.%m.%Y')})"
            else:
                record.date_range_display = "Period not defined"

    def _create_salesperson_success_chart(self, data):
        """Create chart showing success rate by salesperson"""
        if not data:
            return False

        try:
            plt.figure(figsize=(15, 8))

            # Create data arrays
            x_values = [str(d['user_id']) for d in data]
            success_rates = [d['success_rate'] for d in data]
            total_orders = [d['total_orders'] for d in data]

            # Create bar chart
            bars = plt.bar(x_values, success_rates, color='#4CAF50', alpha=0.7)

            # Add value labels above bars
            for i, (bar, orders) in enumerate(zip(bars, total_orders)):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width() / 2, height + 2,
                         f'{orders}',
                         ha='right', va='bottom',
                         rotation=90,
                         fontsize=10,
                         )

            plt.title('Success Rate by Salesperson\n(numbers show total orders)',
                      pad=20, fontsize=12)
            plt.xlabel('Salesperson ID', fontsize=10)
            plt.ylabel('Success Rate (%)', fontsize=10)

            # Add grid
            plt.grid(True, axis='y', linestyle='--', alpha=0.7)

            # Rotate x labels
            plt.xticks(rotation=45, ha='right')

            # Adjust layout and y-axis limit
            plt.ylim(0, max(success_rates) * 1.15)
            plt.tight_layout()

            # Save chart
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
            plt.close()

            return base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error creating salesperson success chart: {str(e)}")
            return False
        finally:
            plt.close('all')

    def _create_partners_rate_chart(self, partner_success_rates):
        """Create bar chart showing distribution of partners by success rate ranges"""
        try:
            # Define success rate ranges with specific order
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
                '#43a047',  # Very dark green
            ]

            # Calculate distribution
            distribution = defaultdict(int)
            for rate in partner_success_rates.values():
                for range_name, (min_val, max_val) in success_ranges:
                    if min_val <= rate <= max_val:
                        distribution[range_name] += 1
                        break

            # Create ordered dictionary for success rate ranges
            ordered_distribution = {range_name: distribution.get(range_name, 0)
                                    for range_name, _ in success_ranges}

            # Create the chart
            plt.figure(figsize=(12, 6))
            plt.bar(ordered_distribution.keys(),
                    ordered_distribution.values(),
                    color=green_shades)
            plt.title('Distribution of Partners by Success Rate Ranges')
            plt.xlabel('Success Rate Range')
            plt.ylabel('Number of Partners')
            plt.xticks(rotation=45)

            # Save the chart
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight')
            plt.close()

            return base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error creating partners rate chart: {str(e)}")
            return False
        finally:
            plt.close('all')

    def _create_partners_rate_plot(self, partner_success_rates):
        """Create line plot showing success rate distribution across partners"""
        plt.figure(figsize=(12, 6))

        # Sort success rates for better visualization
        sorted_rates = sorted(partner_success_rates.values())
        x_values = range(1, len(sorted_rates) + 1)

        plt.plot(x_values, sorted_rates, 'b-', linewidth=2)
        plt.title('Partners Success Rate Distribution')
        plt.xlabel('Number of Partners')
        plt.ylabel('Success Rate (%)')
        plt.grid(True)

        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        plt.close()

        return base64.b64encode(buffer.getvalue())

    def _compute_monthly_charts(self):
        for record in self:
            if not record.data_file:
                record.monthly_analysis_chart = False
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
                month_data['rate'] = (month_data['successful'] / month_data['orders'] * 100) if month_data[
                                                                                                    'orders'] > 0 else 0

            # Sort months chronologically
            sorted_months = sorted(monthly_data.keys(),
                                   key=lambda x: datetime.strptime(x, '%m/%Y'))

            # Create data arrays in chronological order
            months = sorted_months
            orders_data = [monthly_data[month]['orders'] for month in months]
            successful_data = [monthly_data[month]['successful'] for month in months]
            rate_data = [monthly_data[month]['rate'] for month in months]

            if not months:
                record.monthly_analysis_chart = False
                continue

            # Create combined chart
            record.monthly_analysis_chart = record._create_chart(
                months, orders_data, successful_data, rate_data)

    @api.depends('data_file')
    def _compute_cumulative_monthly_charts(self):
        for record in self:
            if not record.data_file:
                record.cumulative_monthly_analysis_chart = False
                continue

            try:
                # Read CSV data
                csv_data = base64.b64decode(record.data_file)
                csv_file = StringIO(csv_data.decode('utf-8'))
                reader = csv.DictReader(csv_file)

                # Prepare monthly data
                monthly_data = {}
                for row in reader:
                    # Використовуємо date_order замість order_date і обрізаємо час
                    date = datetime.strptime(row['date_order'].split()[0], '%Y-%m-%d')
                    month_key = date.strftime('%m/%Y')

                    if month_key not in monthly_data:
                        monthly_data[month_key] = {
                            'orders': 0,
                            'successful': 0,
                            'rate': 0
                        }

                    monthly_data[month_key]['orders'] += 1
                    if row['state'] == 'sale':  # Змінено з 'success' на 'sale'
                        monthly_data[month_key]['successful'] += 1

                # Calculate success rates
                for month in monthly_data:
                    total = monthly_data[month]['orders']
                    successful = monthly_data[month]['successful']
                    monthly_data[month]['rate'] = (successful / total * 100) if total > 0 else 0

                # Sort months chronologically
                sorted_months = sorted(monthly_data.keys(),
                                       key=lambda x: datetime.strptime(x, '%m/%Y'))

                # Create data arrays in chronological order
                months = sorted_months
                orders_data = [monthly_data[month]['orders'] for month in months]
                successful_data = [monthly_data[month]['successful'] for month in months]
                rate_data = [monthly_data[month]['rate'] for month in months]

                if not months:
                    record.cumulative_monthly_analysis_chart = False
                    continue

                # Calculate cumulative values
                x = np.arange(len(months))
                months_display = [datetime.strptime(m, '%m/%Y').strftime('%B %Y') for m in months]
                cumulative_orders = np.cumsum(orders_data)
                cumulative_successful = np.cumsum(successful_data)
                cumulative_rates = [100.0 * s / t if t > 0 else 0
                                    for s, t in zip(cumulative_successful, cumulative_orders)]

                # Create cumulative chart
                fig, ax1 = plt.subplots(figsize=(15, 8))
                ax1.set_xticks(x)
                ax1.set_xticklabels(months_display, rotation=90, ha='center')

                # Створюємо другу вісь Y
                ax2 = ax1.twinx()

                # Графіки для кількості замовлень (ліва вісь)
                line1 = ax1.plot(x, cumulative_orders, marker='o', color='skyblue',
                                 linewidth=2, label='Total Orders')
                line2 = ax1.plot(x, cumulative_successful, marker='o', color='gold',
                                 linewidth=2, label='Successful Orders')

                # Графік для відсотків (права вісь)
                line3 = ax2.plot(x, cumulative_rates, marker='o', color='purple',
                                 linewidth=2, label='Success Rate (%)')

                # Налаштування лівої осі (кількість)
                ax1.set_xlabel('Month')
                ax1.set_ylabel('Count')
                ax1.tick_params(axis='y', labelcolor='black')

                # Налаштування правої осі (відсотки)
                ax2.set_ylabel('Success Rate (%)')
                ax2.tick_params(axis='y', labelcolor='purple')

                # Об'єднуємо легенди з обох осей
                lines = line1 + line2 + line3
                labels = [l.get_label() for l in lines]
                ax1.legend(lines, labels, loc='upper left')

                plt.title('Cumulative Monthly Analysis')
                plt.grid(True)
                plt.subplots_adjust(bottom=0.2)
                plt.tight_layout()

                # Save chart
                buffer = BytesIO()
                plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
                plt.close()
                record.cumulative_monthly_analysis_chart = base64.b64encode(buffer.getvalue())

            except Exception as e:
                print(f'Error computing cumulative monthly charts: {e.__class__}: {e}')
                record.cumulative_monthly_analysis_chart = False
                continue
            finally:
                plt.close('all')

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
            ax1.set_xticks(x)
            ax1.set_xticklabels(months_display, rotation=90, ha='center')

            # Add grid
            ax1.grid(True, axis='y', linestyle='--', alpha=0.7)

            # Add legends
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

            # Adjust layout and y-axis limit
            plt.ylim(0, max(successful_data) * 1.15)
            plt.subplots_adjust(bottom=0.2)
            plt.tight_layout()

            # Save chart
            buffer = BytesIO()
            fig.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
            plt.close()

            return base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error creating chart: {str(e)}")
            return False
        finally:
            plt.close('all')

    def _create_distribution_chart(self, data, title, xlabel, ylabel, colors):
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
                ax.text(bar.get_x() + bar.get_width() / 2., height,
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

    def _create_weekday_success_chart(self, weekday_stats):
        """Creating success rate chart by weekday"""
        try:
            plt.figure(figsize=(12, 6))

            # Weekday names
            weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            success_rates = []
            total_orders = []

            # Calculate success rate
            for day in range(7):
                stats = weekday_stats[day]
                success_rate = (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0
                success_rates.append(success_rate)
                total_orders.append(stats['total'])

            # Create main bars
            bars = plt.bar(weekdays, success_rates, color='#4CAF50', alpha=0.7)

            # Add order count labels
            for i, (bar, orders) in enumerate(zip(bars, total_orders)):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width() / 2, height + 1,
                         f'{orders}',
                         ha='center', va='bottom',
                         rotation=0,
                         fontsize=10,
                         color='green')

            plt.title('Success Rate by Weekday\n(numbers show total orders)',
                      pad=20, fontsize=12)
            plt.xlabel('Weekday')
            plt.ylabel('Success Rate (%)')

            # Add grid
            plt.grid(True, linestyle='--', alpha=0.7, zorder=0)

            # Configure X axis labels
            plt.xticks(rotation=45, ha='right')

            # Set Y axis limits
            plt.ylim(0, max(success_rates) * 1.15)

            # Configure layout
            plt.tight_layout()

            # Save chart
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
            plt.close()

            return base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error creating weekday success chart: {str(e)}")
            return False

    def _create_month_success_chart(self, month_stats):
        """Creating success rate chart by month"""
        try:
            plt.figure(figsize=(12, 6))

            # Month names
            months = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
            success_rates = []
            total_orders = []

            # Calculate success rate
            for month in range(1, 13):
                stats = month_stats[month]
                success_rate = (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0
                success_rates.append(success_rate)
                total_orders.append(stats['total'])

            # Create main bars
            bars = plt.bar(months, success_rates, color='#2196F3', alpha=0.7)

            # Add order count labels
            for i, (bar, orders) in enumerate(zip(bars, total_orders)):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width() / 2, height + 1,
                         f'{orders}',
                         ha='center', va='bottom',
                         rotation=0,
                         fontsize=10,
                         color='blue')

            plt.title('Success Rate by Month\n(numbers show total orders)',
                      pad=20, fontsize=12)
            plt.xlabel('Month')
            plt.ylabel('Success Rate (%)')

            # Add grid
            plt.grid(True, linestyle='--', alpha=0.7, zorder=0)

            # Configure X axis labels
            plt.xticks(rotation=45)

            # Set Y axis limits
            plt.ylim(0, max(success_rates) * 1.15)

            # Configure layout
            plt.tight_layout()

            # Save chart
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
            plt.close()

            return base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error creating month success chart: {str(e)}")
            return False

    def _compute_weekday_charts(self):
        for record in self:
            if not record.data_file:
                record.weekday_success_chart = False
                continue

            # Read CSV data
            data = record._read_csv_data()
            if not data:
                continue

            # Initialize weekday data
            weekday_data = defaultdict(lambda: {'total': 0, 'successful': 0})

            # Process data
            for row in data:
                if not row['date_order']:
                    continue

                weekday = row['date_order'].weekday()
                weekday_data[weekday]['total'] += 1
                if row['state'] == 'sale':
                    weekday_data[weekday]['successful'] += 1

            # Create weekday success chart
            record.weekday_success_chart = record._create_weekday_success_chart(weekday_data)

    def _compute_month_charts(self):
        for record in self:
            if not record.data_file:
                record.month_success_chart = False
                continue

            # Read CSV data
            data = record._read_csv_data()
            if not data:
                continue

            # Initialize month data
            month_data = defaultdict(lambda: {'total': 0, 'successful': 0})

            # Process data
            for row in data:
                if not row['date_order']:
                    continue

                month = row['date_order'].month
                month_data[month]['total'] += 1
                if row['state'] == 'sale':
                    month_data[month]['successful'] += 1

            # Create month success chart
            record.month_success_chart = record._create_month_success_chart(month_data)

    def _compute_partner_orders_charts(self):
        """Compute success rate based on total number of partner orders"""
        for record in self:
            if not record.data_file:
                record.partner_orders_success_chart = False
                continue

            try:
                # Read CSV data
                data = record._read_csv_data()
                if not data:
                    continue

                # Calculate statistics per partner
                partner_stats = {}
                for row in data:
                    partner_id = row['partner_id']
                    if partner_id not in partner_stats:
                        partner_stats[partner_id] = {'total': 0, 'successful': 0}

                    partner_stats[partner_id]['total'] += 1
                    if row['state'] == 'sale':
                        partner_stats[partner_id]['successful'] += 1

                # Create chart
                record.partner_orders_success_chart = record._create_partner_orders_success_chart(partner_stats)

            except Exception as e:
                print(f"Error computing partner orders success chart: {str(e)}")
                record.partner_orders_success_chart = False

    def _create_partner_orders_success_chart(self, partner_stats):
        """Create chart showing success rate by total number of partner orders"""
        try:
            plt.figure(figsize=(12, 6))

            # Calculate success rates and total orders
            success_data = []
            for partner_id, stats in partner_stats.items():
                if stats['total'] > 0:
                    success_rate = (stats['successful'] / stats['total']) * 100
                    success_data.append((stats['total'], success_rate))

            # Sort by total orders
            success_data.sort(key=lambda x: x[0])

            total_points = len(success_data)
            if total_points == 0:
                return False

            # Визначаємо кількість груп (зменшуємо якщо партнерів мало)
            num_groups = min(30, total_points // 20)  # Мінімум 20 партнерів на групу
            if num_groups < 5:  # Якщо груп менше 5, встановлюємо мінімум 5 груп
                num_groups = 5

            # Розраховуємо розмір кожної групи
            group_size = total_points // num_groups
            remainder = total_points % num_groups

            # Ініціалізуємо результат
            result = {
                'ranges': [],
                'rates': [],
                'orders_count': []
            }

            # Розбиваємо на групи
            start_idx = 0
            for i in range(num_groups):
                current_group_size = group_size + (1 if i < remainder else 0)
                if current_group_size == 0:
                    break

                end_idx = start_idx + current_group_size
                group_points = success_data[start_idx:end_idx]

                # Рахуємо статистику для групи
                min_orders = group_points[0][0]
                max_orders = group_points[-1][0]
                avg_success_rate = sum(rate for _, rate in group_points) / len(group_points)

                # Форматуємо діапазон
                if max_orders >= 100:
                    range_str = f'{min_orders}-{max_orders}'
                else:
                    range_str = f'{min_orders}-{max_orders}'

                # Додаємо дані до результату
                result['ranges'].append(range_str)
                result['rates'].append(avg_success_rate)
                result['orders_count'].append(len(group_points))

                start_idx = end_idx

            # Створюємо точковий графік
            x_points = []
            y_points = []
            counts = []
            for i, (rate, count) in enumerate(zip(result['rates'], result['orders_count'])):
                if count > 0:
                    x_points.append(i)
                    y_points.append(rate)
                    counts.append(count)

            # Створюємо градієнт кольорів від червоного до зеленого в залежності від success rate
            colors = ['#ff4d4d' if rate < 50 else '#00cc00' for rate in y_points]
            sizes = [max(80, min(150, count / 2)) for count in counts]  # Розмір точки залежить від кількості партнерів

            # Малюємо точки
            scatter = plt.scatter(x_points, y_points, s=sizes, alpha=0.6, c=colors)

            # Розраховуємо середню кількість партнерів на точку
            avg_partners = sum(counts) // len(counts) if counts else 0

            plt.title(
                f'Success Rate by Number of Orders per Partner\n(each point represents ~{avg_partners} partners, point size shows relative number in range)',
                pad=20, fontsize=12)
            plt.xlabel('Number of Orders')
            plt.ylabel('Success Rate (%)')

            # Налаштовуємо осі
            plt.ylim(-5, 105)

            # Показуємо всі мітки, якщо їх менше 10, інакше кожну другу
            if len(result['ranges']) <= 10:
                plt.xticks(range(len(result['ranges'])), result['ranges'],
                           rotation=45, ha='right')
            else:
                plt.xticks(range(len(result['ranges']))[::2],
                           [result['ranges'][i] for i in range(0, len(result['ranges']), 2)],
                           rotation=45, ha='right')

            plt.grid(True, linestyle='--', alpha=0.7)

            # Додаємо горизонтальні лінії
            plt.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
            plt.axhline(y=50, color='gray', linestyle='--', alpha=0.3)
            plt.axhline(y=100, color='gray', linestyle='-', alpha=0.3)

            # Додаємо легенду
            legend_elements = [
                plt.Line2D([0], [0], marker='o', color='w',
                           markerfacecolor='#ff4d4d', markersize=10,
                           label='Success Rate < 50%'),
                plt.Line2D([0], [0], marker='o', color='w',
                           markerfacecolor='#00cc00', markersize=10,
                           label='Success Rate ≥ 50%')
            ]
            plt.legend(handles=legend_elements, loc='upper right')

            # Зберігаємо графік
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight',
                        dpi=100, pad_inches=0.2)
            plt.close()

            return base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error creating partner orders success chart: {str(e)}")
            return False

    def _compute_amount_success_charts(self):
        """Compute success rate based on different amount metrics"""
        for record in self:
            if not record.data_file:
                record.total_amount_success_chart = False
                record.success_amount_success_chart = False
                record.avg_amount_success_chart = False
                record.avg_success_amount_success_chart = False
                continue

            try:
                # Read CSV data
                data = record._read_csv_data()
                if not data:
                    continue

                # Calculate statistics per partner
                partner_stats = {}
                for row in data:
                    partner_id = row['partner_id']
                    amount = float(row['amount_total'])

                    if partner_id not in partner_stats:
                        partner_stats[partner_id] = {
                            'total_orders': 0,
                            'successful_orders': 0,
                            'total_amount': 0,
                            'success_amount': 0
                        }

                    partner_stats[partner_id]['total_orders'] += 1
                    partner_stats[partner_id]['total_amount'] += amount

                    if row['state'] == 'sale':
                        partner_stats[partner_id]['successful_orders'] += 1
                        partner_stats[partner_id]['success_amount'] += amount

                # Calculate success rates and averages
                for partner_id, stats in partner_stats.items():
                    stats['success_rate'] = (stats['successful_orders'] / stats['total_orders'] * 100) if stats[
                                                                                                              'total_orders'] > 0 else 0
                    stats['avg_amount'] = stats['total_amount'] / stats['total_orders'] if stats[
                                                                                               'total_orders'] > 0 else 0
                    stats['avg_success_amount'] = stats['success_amount'] / stats['successful_orders'] if stats[
                                                                                                              'successful_orders'] > 0 else 0

                # Create charts
                record.total_amount_success_chart = record._create_amount_based_chart(
                    partner_stats, 'total_amount',
                    'Success Rate by Total Orders Amount',
                    'Total Orders Amount'
                )

                record.success_amount_success_chart = record._create_amount_based_chart(
                    partner_stats, 'success_amount',
                    'Success Rate by Successful Orders Amount',
                    'Successful Orders Amount'
                )

                record.avg_amount_success_chart = record._create_amount_based_chart(
                    partner_stats, 'avg_amount',
                    'Success Rate by Average Order Amount',
                    'Average Order Amount'
                )

                record.avg_success_amount_success_chart = record._create_amount_based_chart(
                    partner_stats, 'avg_success_amount',
                    'Success Rate by Average Successful Order Amount',
                    'Average Successful Order Amount'
                )


            except Exception as e:
                print(f"Error computing amount success charts: {str(e)}")
                record.total_amount_success_chart = False
                record.success_amount_success_chart = False
                record.avg_amount_success_chart = False
                record.avg_success_amount_success_chart = False

    def _create_amount_based_chart(self, partner_stats, amount_field, title, xlabel):
        """Create chart showing success rate by specified amount metric"""
        try:
            plt.figure(figsize=(15, 8))

            # Prepare data
            data_points = []
            for partner_id, stats in partner_stats.items():
                amount = stats[amount_field]
                if amount > 0:  # Виключаємо записи з нульовою сумою
                    data_points.append((amount, stats['success_rate']))

            if not data_points:
                return False

            # Sort by amount
            data_points.sort(key=lambda x: x[0])

            total_points = len(data_points)
            if total_points == 0:
                return False

            # Визначаємо кількість груп (зменшуємо якщо партнерів мало)
            num_groups = min(30, total_points // 20)  # Мінімум 20 партнерів на групу
            if num_groups < 5:  # Якщо груп менше 5, встановлюємо мінімум 5 груп
                num_groups = 5

            # Розраховуємо розмір кожної групи
            group_size = total_points // num_groups
            remainder = total_points % num_groups

            # Ініціалізуємо результат
            result = {
                'ranges': [],
                'rates': [],
                'orders_count': []
            }

            # Розбиваємо на групи
            start_idx = 0
            for i in range(num_groups):
                # Додаємо +1 до розміру групи для перших remainder груп
                current_group_size = group_size + (1 if i < remainder else 0)
                if current_group_size == 0:
                    break

                end_idx = start_idx + current_group_size
                group_points = data_points[start_idx:end_idx]

                # Рахуємо статистику для групи
                min_amount = group_points[0][0]
                max_amount = group_points[-1][0]
                avg_success_rate = sum(rate for _, rate in group_points) / len(group_points)

                # Форматуємо діапазон
                if max_amount >= 1000000:
                    range_str = f'{min_amount / 1000000:.1f}M-{max_amount / 1000000:.1f}M'
                elif max_amount >= 1000:
                    range_str = f'{min_amount / 1000:.0f}K-{max_amount / 1000:.0f}K'
                else:
                    range_str = f'{min_amount:.0f}-{max_amount:.0f}'

                # Додаємо дані до результату
                result['ranges'].append(range_str)
                result['rates'].append(avg_success_rate)
                result['orders_count'].append(len(group_points))

                start_idx = end_idx

            # Створюємо точковий графік
            x_points = []
            y_points = []
            counts = []
            for i, (rate, count) in enumerate(zip(result['rates'], result['orders_count'])):
                if count > 0:
                    x_points.append(i)
                    y_points.append(rate)
                    counts.append(count)

            # Створюємо градієнт кольорів від червоного до зеленого в залежності від success rate
            colors = ['#ff4d4d' if rate < 50 else '#00cc00' for rate in y_points]
            sizes = [max(80, min(150, count / 2)) for count in counts]  # Розмір точки залежить від кількості партнерів

            # Малюємо точки
            scatter = plt.scatter(x_points, y_points, s=sizes, alpha=0.6, c=colors)

            # Розраховуємо середню кількість партнерів на точку
            avg_partners = sum(counts) // len(counts) if counts else 0

            plt.title(
                f'{title}\n(each point represents ~{avg_partners} partners, point size shows relative number in range)',
                pad=20, fontsize=12)
            plt.xlabel(xlabel)
            plt.ylabel('Success Rate (%)')

            # Налаштовуємо осі
            plt.ylim(-5, 105)

            # Показуємо всі мітки, якщо їх менше 10, інакше кожну другу
            if len(result['ranges']) <= 10:
                plt.xticks(range(len(result['ranges'])), result['ranges'],
                           rotation=45, ha='right')
            else:
                plt.xticks(range(len(result['ranges']))[::2],
                           [result['ranges'][i] for i in range(0, len(result['ranges']), 2)],
                           rotation=45, ha='right')

            plt.grid(True, linestyle='--', alpha=0.7)

            # Додаємо горизонтальні лінії
            plt.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
            plt.axhline(y=50, color='gray', linestyle='--', alpha=0.3)
            plt.axhline(y=100, color='gray', linestyle='-', alpha=0.3)

            # Додаємо легенду
            legend_elements = [
                plt.Line2D([0], [0], marker='o', color='w',
                           markerfacecolor='#ff4d4d', markersize=10,
                           label='Success Rate < 50%'),
                plt.Line2D([0], [0], marker='o', color='w',
                           markerfacecolor='#00cc00', markersize=10,
                           label='Success Rate ≥ 50%')
            ]
            plt.legend(handles=legend_elements, loc='upper right')

            # Зберігаємо графік
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight',
                        dpi=100, pad_inches=0.2)
            plt.close()

            return base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error creating amount based chart: {str(e)}")
            return False

    def _format_amount(self, amount):
        """Format amount for display in chart labels"""
        if amount >= 1000000:
            return f'{amount / 1000000:.1f}M'
        elif amount >= 1000:
            return f'{amount / 1000:.0f}K'
        else:
            return f'{amount:.0f}'

    @api.depends('data_file')
    def _compute_cumulative_success_rate_chart(self):
        """Compute cumulative success rate chart over time"""
        for record in self:
            if not record.data_file:
                record.cumulative_success_rate_chart = False
                continue

            try:
                # Read CSV data
                data = record._read_csv_data()
                if not data:
                    continue

                # Convert dates and sort by date
                orders_data = []
                for row in data:
                    if isinstance(row['date_order'], str):
                        order_date = datetime.strptime(row['date_order'], '%Y-%m-%d %H:%M:%S')
                    else:
                        order_date = row['date_order']
                    orders_data.append({
                        'date': order_date,
                        'success': row['state'] == 'sale'
                    })

                # Sort orders by date
                orders_data.sort(key=lambda x: x['date'])

                if not orders_data:
                    continue

                # Generate monthly points from start to end
                start_date = orders_data[0]['date'].replace(day=1, hour=0, minute=0, second=0)
                end_date = orders_data[-1]['date'].replace(day=1, hour=0, minute=0, second=0)

                current_date = start_date
                points_data = []
                cumulative_orders = 0
                cumulative_success = 0

                while current_date <= end_date:
                    next_date = (current_date.replace(day=1) + relativedelta(months=1)).replace(day=1)

                    # Count orders up to this date
                    while orders_data and orders_data[0]['date'] < next_date:
                        order = orders_data.pop(0)
                        cumulative_orders += 1
                        if order['success']:
                            cumulative_success += 1

                    if cumulative_orders > 0:
                        success_rate = (cumulative_success / cumulative_orders) * 100
                        points_data.append((current_date, success_rate, cumulative_orders))

                    current_date = next_date

                # Create the chart
                plt.figure(figsize=(15, 8))

                # Prepare data for plotting
                dates = [point[0] for point in points_data]
                rates = [point[1] for point in points_data]
                orders = [point[2] for point in points_data]

                # Convert dates to matplotlib format
                dates_num = [plt.matplotlib.dates.date2num(date) for date in dates]

                # Calculate point sizes based on number of orders
                max_size = 150
                min_size = 50
                sizes = [min(max_size, max(min_size, orders_count / 10)) for orders_count in orders]

                # Create scatter plot with connected lines
                plt.plot(dates_num, rates, 'b-', alpha=0.3)  # Line connecting points
                scatter = plt.scatter(dates_num, rates, s=sizes, alpha=0.6,
                                      c=rates, cmap='RdYlGn',
                                      norm=plt.Normalize(0, 100))

                # Customize the chart
                plt.title('Cumulative Success Rate Over Time\n(point size shows total orders up to that date)',
                          pad=20, fontsize=12)
                plt.xlabel('Date')
                plt.ylabel('Cumulative Success Rate (%)')

                # Format x-axis
                plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%b %Y'))
                plt.xticks(rotation=45, ha='right')

                # Set y-axis limits
                plt.ylim(-5, 105)

                # Add grid
                plt.grid(True, linestyle='--', alpha=0.7)

                # Add horizontal lines
                plt.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
                plt.axhline(y=50, color='gray', linestyle='--', alpha=0.3)
                plt.axhline(y=100, color='gray', linestyle='-', alpha=0.3)

                # Add colorbar
                cbar = plt.colorbar(scatter)
                cbar.set_label('Success Rate (%)')

                # Add static annotations for all points
                for i, (date, rate, order_count) in enumerate(points_data):
                    # Add annotation every 6 months (every 6th point)
                    if i % 6 == 0:
                        plt.annotate(f'{rate:.1f}%\n{order_count} orders',
                                     (dates_num[i], rate),
                                     xytext=(0, 10), textcoords='offset points',
                                     ha='center',
                                     bbox=dict(boxstyle='round,pad=0.5', fc='white', alpha=0.8, ec='none'),
                                     fontsize=8)

                # Adjust layout to prevent overlapping
                plt.tight_layout()

                # Save the chart
                buffer = BytesIO()
                plt.savefig(buffer, format='png', bbox_inches='tight',
                            dpi=100, pad_inches=0.2)
                plt.close()

                record.cumulative_success_rate_chart = base64.b64encode(buffer.getvalue())

            except Exception as e:
                print(f"Error computing cumulative success rate chart: {str(e)}")
                record.cumulative_success_rate_chart = False
                plt.close('all')

    def _compute_order_intensity_chart(self):
        for record in self:
            try:
                # Read CSV data
                data = record._read_csv_data()
                if not data:
                    record.order_intensity_success_chart = False
                    continue

                # Calculate metrics for each partner
                partner_stats = defaultdict(lambda: {
                    'first_order': None,
                    'last_order': None,
                    'total': 0,
                    'success': 0
                })

                # Collect statistics for each partner
                for row in data:
                    partner_id = row['partner_id']
                    order_date = row['date_order']

                    stats = partner_stats[partner_id]
                    if not stats['first_order'] or order_date < stats['first_order']:
                        stats['first_order'] = order_date
                    if not stats['last_order'] or order_date > stats['last_order']:
                        stats['last_order'] = order_date

                    stats['total'] += 1
                    if row['state'] == 'sale':
                        stats['success'] += 1

                # Calculate success rate and intensity for each partner
                partner_metrics = []
                for partner_id, stats in partner_stats.items():
                    if stats['first_order'] and stats['last_order'] and stats['total'] > 0:
                        # Calculate months between first and last order
                        months_active = ((stats['last_order'] - stats['first_order']).days / 30.44) + 1

                        # Calculate order intensity (orders per month)
                        intensity = stats['total'] / months_active

                        # Calculate success rate
                        success_rate = (stats['success'] / stats['total'] * 100)

                        partner_metrics.append({
                            'intensity': intensity,
                            'success_rate': success_rate
                        })

                if not partner_metrics:
                    print("No data to plot")
                    record.order_intensity_success_chart = False
                    continue

                # Find min and max success rates
                min_rate = min(p['success_rate'] for p in partner_metrics)
                max_rate = max(p['success_rate'] for p in partner_metrics)

                # Create 20 equal ranges of success rate
                num_groups = 20
                rate_step = (max_rate - min_rate) / num_groups

                # Initialize groups
                grouped_metrics = []
                for i in range(num_groups):
                    rate_min = min_rate + i * rate_step
                    rate_max = min_rate + (i + 1) * rate_step
                    group = [p for p in partner_metrics
                             if rate_min <= p['success_rate'] < rate_max]

                    if group:  # Only add group if it has partners
                        avg_intensity = sum(p['intensity'] for p in group) / len(group)
                        avg_success_rate = sum(p['success_rate'] for p in group) / len(group)

                        grouped_metrics.append({
                            'intensity': avg_intensity,
                            'success_rate': avg_success_rate,
                            'partners_count': len(group)
                        })

                # Create the chart
                plt.figure(figsize=(12, 8))

                # Extract data for plotting
                intensities = [d['intensity'] for d in grouped_metrics]
                success_rates = [d['success_rate'] for d in grouped_metrics]
                partners_counts = [d['partners_count'] for d in grouped_metrics]

                # Create scatter plot
                plt.scatter(intensities, success_rates,
                            s=100,  # Fixed size for better readability
                            alpha=0.6)

                # Add trend line
                z = np.polyfit(intensities, success_rates, 1)
                p = np.poly1d(z)
                plt.plot(intensities, p(intensities), "r--", alpha=0.8)

                # Add annotations for each point
                for i, (x, y, count) in enumerate(zip(intensities, success_rates, partners_counts)):
                    plt.annotate(
                        f"{count} clients",
                        (x, y),
                        xytext=(5, 5), textcoords='offset points',
                        bbox=dict(facecolor='white', edgecolor='none', alpha=0.7)
                    )

                plt.xlabel('Інтенсивність замовлень (замовлень на місяць)')
                plt.ylabel('Середній відсоток успішних замовлень (%)')
                plt.title('Залежність успішності від інтенсивності замовлень\n(кожна точка представляє групу клієнтів)')
                plt.grid(True, linestyle='--', alpha=0.7)

                # Save the chart
                buffer = BytesIO()
                plt.savefig(buffer, format='png', bbox_inches='tight',
                            dpi=100, pad_inches=0.2)
                plt.close()

                record.order_intensity_success_chart = base64.b64encode(buffer.getvalue())

            except Exception as e:
                print(f"Error computing order intensity chart: {str(e)}")
                record.order_intensity_success_chart = False
                plt.close('all')

    def _compute_success_order_intensity_chart(self):
        for record in self:
            try:
                # Read CSV data
                data = record._read_csv_data()
                if not data:
                    record.success_order_intensity_chart = False
                    continue

                # Calculate metrics for each partner
                partner_stats = defaultdict(lambda: {
                    'first_order': None,
                    'last_order': None,
                    'total': 0,
                    'success': 0
                })

                # Collect statistics for each partner
                for row in data:
                    partner_id = row['partner_id']
                    order_date = row['date_order']

                    stats = partner_stats[partner_id]
                    if not stats['first_order'] or order_date < stats['first_order']:
                        stats['first_order'] = order_date
                    if not stats['last_order'] or order_date > stats['last_order']:
                        stats['last_order'] = order_date

                    stats['total'] += 1
                    if row['state'] == 'sale':
                        stats['success'] += 1

                # Calculate success rate and intensity for each partner
                partner_metrics = []
                for partner_id, stats in partner_stats.items():
                    if stats['first_order'] and stats['last_order'] and stats['success'] > 0:
                        # Calculate months between first and last successful order
                        months_active = ((stats['last_order'] - stats['first_order']).days / 30.44) + 1

                        # Calculate success order intensity (successful orders per month)
                        success_intensity = stats['success'] / months_active

                        # Calculate success rate
                        success_rate = (stats['success'] / stats['total'] * 100)

                        partner_metrics.append({
                            'intensity': success_intensity,
                            'success_rate': success_rate
                        })

                if not partner_metrics:
                    print("No data to plot")
                    record.success_order_intensity_chart = False
                    continue

                # Find min and max success rates
                min_rate = min(p['success_rate'] for p in partner_metrics)
                max_rate = max(p['success_rate'] for p in partner_metrics)

                # Create 20 equal ranges of success rate
                num_groups = 20
                rate_step = (max_rate - min_rate) / num_groups

                # Initialize groups
                grouped_metrics = []
                for i in range(num_groups):
                    rate_min = min_rate + i * rate_step
                    rate_max = min_rate + (i + 1) * rate_step
                    group = [p for p in partner_metrics
                             if rate_min <= p['success_rate'] < rate_max]

                    if group:  # Only add group if it has partners
                        avg_intensity = sum(p['intensity'] for p in group) / len(group)
                        avg_success_rate = sum(p['success_rate'] for p in group) / len(group)

                        grouped_metrics.append({
                            'intensity': avg_intensity,
                            'success_rate': avg_success_rate,
                            'partners_count': len(group)
                        })

                # Create the chart
                plt.figure(figsize=(12, 8))

                # Extract data for plotting
                intensities = [d['intensity'] for d in grouped_metrics]
                success_rates = [d['success_rate'] for d in grouped_metrics]
                partners_counts = [d['partners_count'] for d in grouped_metrics]

                # Create scatter plot
                plt.scatter(intensities, success_rates,
                            s=100,  # Fixed size for better readability
                            alpha=0.6)

                # Add trend line
                z = np.polyfit(intensities, success_rates, 1)
                p = np.poly1d(z)
                plt.plot(intensities, p(intensities), "r--", alpha=0.8)

                # Add annotations for each point
                for i, (x, y, count) in enumerate(zip(intensities, success_rates, partners_counts)):
                    plt.annotate(
                        f"{count} clients",
                        (x, y),
                        xytext=(5, 5), textcoords='offset points',
                        bbox=dict(facecolor='white', edgecolor='none', alpha=0.7)
                    )

                plt.xlabel('Інтенсивність успішних замовлень (успішних замовлень на місяць)')
                plt.ylabel('Середній відсоток успішних замовлень (%)')
                plt.title(
                    'Залежність успішності від інтенсивності успішних замовлень\n(кожна точка представляє групу клієнтів)')
                plt.grid(True, linestyle='--', alpha=0.7)

                # Save the chart
                buffer = BytesIO()
                plt.savefig(buffer, format='png', bbox_inches='tight',
                            dpi=100, pad_inches=0.2)
                plt.close()

                record.success_order_intensity_chart = base64.b64encode(buffer.getvalue())

            except Exception as e:
                print(f"Error computing success order intensity chart: {str(e)}")
                record.success_order_intensity_chart = False
                plt.close('all')

    def _compute_amount_intensity_chart(self):
        for record in self:
            try:
                # Read CSV data
                data = record._read_csv_data()
                if not data:
                    record.amount_intensity_success_chart = False
                    continue

                # Calculate metrics for each partner
                partner_stats = defaultdict(lambda: {
                    'first_order': None,
                    'last_order': None,
                    'total': 0,
                    'success': 0,
                    'total_amount': 0
                })

                # Collect statistics for each partner
                for row in data:
                    partner_id = row['partner_id']
                    order_date = row['date_order']
                    amount = float(row['amount_total'])

                    stats = partner_stats[partner_id]
                    if not stats['first_order'] or order_date < stats['first_order']:
                        stats['first_order'] = order_date
                    if not stats['last_order'] or order_date > stats['last_order']:
                        stats['last_order'] = order_date

                    stats['total'] += 1
                    stats['total_amount'] += amount
                    if row['state'] == 'sale':
                        stats['success'] += 1

                # Calculate success rate and intensity for each partner
                partner_metrics = []
                for partner_id, stats in partner_stats.items():
                    if stats['first_order'] and stats['last_order'] and stats['total'] > 0:
                        # Calculate months between first and last order
                        months_active = ((stats['last_order'] - stats['first_order']).days / 30.44) + 1

                        # Calculate order intensity (orders per month)
                        intensity = stats['total'] / months_active

                        # Calculate amount intensity (amount per month)
                        amount_intensity = stats['total_amount'] / months_active

                        # Calculate success rate
                        success_rate = (stats['success'] / stats['total'] * 100)

                        partner_metrics.append({
                            'intensity': amount_intensity,
                            'success_rate': success_rate
                        })

                if not partner_metrics:
                    print("No data to plot")
                    record.amount_intensity_success_chart = False
                    continue

                # Find min and max success rates
                min_rate = min(p['success_rate'] for p in partner_metrics)
                max_rate = max(p['success_rate'] for p in partner_metrics)

                # Create 20 equal ranges of success rate
                num_groups = 20
                rate_step = (max_rate - min_rate) / num_groups

                # Initialize groups
                grouped_metrics = []
                for i in range(num_groups):
                    rate_min = min_rate + i * rate_step
                    rate_max = min_rate + (i + 1) * rate_step
                    group = [p for p in partner_metrics
                             if rate_min <= p['success_rate'] < rate_max]

                    if group:  # Only add group if it has partners
                        avg_intensity = sum(p['intensity'] for p in group) / len(group)
                        avg_success_rate = sum(p['success_rate'] for p in group) / len(group)

                        grouped_metrics.append({
                            'intensity': avg_intensity,
                            'success_rate': avg_success_rate,
                            'partners_count': len(group)
                        })

                # Create the chart
                plt.figure(figsize=(12, 8))

                # Extract data for plotting
                intensities = [d['intensity'] for d in grouped_metrics]
                success_rates = [d['success_rate'] for d in grouped_metrics]
                partners_counts = [d['partners_count'] for d in grouped_metrics]

                # Create scatter plot
                plt.scatter(intensities, success_rates,
                            s=100,  # Fixed size for better readability
                            alpha=0.6)

                # Add trend line
                z = np.polyfit(intensities, success_rates, 1)
                p = np.poly1d(z)
                plt.plot(intensities, p(intensities), "r--", alpha=0.8)

                # Add annotations for each point
                for i, (x, y, count) in enumerate(zip(intensities, success_rates, partners_counts)):
                    plt.annotate(
                        f"{count} clients",
                        (x, y),
                        xytext=(5, 5), textcoords='offset points',
                        bbox=dict(facecolor='white', edgecolor='none', alpha=0.7)
                    )

                plt.xlabel('Інтенсивність замовлень за сумою (сума замовлень на місяць)')
                plt.ylabel('Середній відсоток успішних замовлень (%)')
                plt.title(
                    'Залежність успішності від інтенсивності замовлень за сумою\n(кожна точка представляє групу клієнтів)')
                plt.grid(True, linestyle='--', alpha=0.7)

                # Save the chart
                buffer = BytesIO()
                plt.savefig(buffer, format='png', bbox_inches='tight',
                            dpi=100, pad_inches=0.2)
                plt.close()

                record.amount_intensity_success_chart = base64.b64encode(buffer.getvalue())

            except Exception as e:
                print(f"Error computing amount intensity chart: {str(e)}")
                record.amount_intensity_success_chart = False
                plt.close('all')

    def _compute_success_amount_intensity_chart(self):
        for record in self:
            try:
                # Read CSV data
                data = record._read_csv_data()
                if not data:
                    record.success_amount_intensity_chart = False
                    continue

                # Calculate metrics for each partner
                partner_stats = defaultdict(lambda: {
                    'first_order': None,
                    'last_order': None,
                    'total': 0,
                    'success': 0,
                    'success_amount': 0
                })

                # Collect statistics for each partner
                for row in data:
                    partner_id = row['partner_id']
                    order_date = row['date_order']
                    amount = float(row['amount_total'])

                    stats = partner_stats[partner_id]
                    if not stats['first_order'] or order_date < stats['first_order']:
                        stats['first_order'] = order_date
                    if not stats['last_order'] or order_date > stats['last_order']:
                        stats['last_order'] = order_date

                    stats['total'] += 1
                    if row['state'] == 'sale':
                        stats['success'] += 1
                        stats['success_amount'] += amount

                # Calculate success rate and intensity for each partner
                partner_metrics = []
                for partner_id, stats in partner_stats.items():
                    if stats['first_order'] and stats['last_order'] and stats['success'] > 0:
                        # Calculate months between first and last successful order
                        months_active = ((stats['last_order'] - stats['first_order']).days / 30.44) + 1

                        # Calculate success order intensity (successful orders per month)
                        success_intensity = stats['success'] / months_active

                        # Calculate success amount intensity (successful amount per month)
                        success_amount_intensity = stats['success_amount'] / months_active

                        # Calculate success rate
                        success_rate = (stats['success'] / stats['total'] * 100)

                        partner_metrics.append({
                            'intensity': success_amount_intensity,
                            'success_rate': success_rate
                        })

                if not partner_metrics:
                    print("No data to plot")
                    record.success_amount_intensity_chart = False
                    continue

                # Find min and max success rates
                min_rate = min(p['success_rate'] for p in partner_metrics)
                max_rate = max(p['success_rate'] for p in partner_metrics)

                # Create 20 equal ranges of success rate
                num_groups = 20
                rate_step = (max_rate - min_rate) / num_groups

                # Initialize groups
                grouped_metrics = []
                for i in range(num_groups):
                    rate_min = min_rate + i * rate_step
                    rate_max = min_rate + (i + 1) * rate_step
                    group = [p for p in partner_metrics
                             if rate_min <= p['success_rate'] < rate_max]

                    if group:  # Only add group if it has partners
                        avg_intensity = sum(p['intensity'] for p in group) / len(group)
                        avg_success_rate = sum(p['success_rate'] for p in group) / len(group)

                        grouped_metrics.append({
                            'intensity': avg_intensity,
                            'success_rate': avg_success_rate,
                            'partners_count': len(group)
                        })

                # Create the chart
                plt.figure(figsize=(12, 8))

                # Extract data for plotting
                intensities = [d['intensity'] for d in grouped_metrics]
                success_rates = [d['success_rate'] for d in grouped_metrics]
                partners_counts = [d['partners_count'] for d in grouped_metrics]

                # Create scatter plot
                plt.scatter(intensities, success_rates,
                            s=100,  # Fixed size for better readability
                            alpha=0.6)

                # Add trend line
                z = np.polyfit(intensities, success_rates, 1)
                p = np.poly1d(z)
                plt.plot(intensities, p(intensities), "r--", alpha=0.8)

                # Add annotations for each point
                for i, (x, y, count) in enumerate(zip(intensities, success_rates, partners_counts)):
                    plt.annotate(
                        f"{count} clients",
                        (x, y),
                        xytext=(5, 5), textcoords='offset points',
                        bbox=dict(facecolor='white', edgecolor='none', alpha=0.7)
                    )

                plt.xlabel('Інтенсивність успішних замовлень за сумою (сума успішних замовлень на місяць)')
                plt.ylabel('Середній відсоток успішних замовлень (%)')
                plt.title(
                    'Залежність успішності від інтенсивності успішних замовлень за сумою\n(кожна точка представляє групу клієнтів)')
                plt.grid(True, linestyle='--', alpha=0.7)

                # Save the chart
                buffer = BytesIO()
                plt.savefig(buffer, format='png', bbox_inches='tight',
                            dpi=100, pad_inches=0.2)
                plt.close()

                record.success_amount_intensity_chart = base64.b64encode(buffer.getvalue())

            except Exception as e:
                print(f"Error computing success amount intensity chart: {str(e)}")
                record.success_amount_intensity_chart = False
                plt.close('all')

    def _compute_monthly_success_rate_chart(self):
        """Compute chart showing success rate for each month"""
        for record in self:
            if not record.data_file:
                record.monthly_success_rate_chart = False
                continue

            try:
                # Read CSV data
                data = record._read_csv_data()
                if not data:
                    continue

                # Group orders by month
                monthly_stats = defaultdict(lambda: {'total': 0, 'success': 0})

                # Collect statistics for each month
                for row in data:
                    order_date = row['date_order']
                    month_key = order_date.strftime('%Y-%m')

                    monthly_stats[month_key]['total'] += 1
                    if row['state'] == 'sale':
                        monthly_stats[month_key]['success'] += 1

                if not monthly_stats:
                    print("No data to plot")
                    record.monthly_success_rate_chart = False
                    continue

                # Calculate success rate for each month
                months = sorted(monthly_stats.keys())
                success_rates = []
                total_orders = []

                for month in months:
                    stats = monthly_stats[month]
                    success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
                    success_rates.append(success_rate)
                    total_orders.append(stats['total'])

                # Create the chart
                plt.figure(figsize=(15, 8))

                # Create scatter plot for success rates
                ax1 = plt.gca()
                scatter = ax1.scatter(months, success_rates, color='tab:blue', s=100, alpha=0.6)
                ax1.plot(months, success_rates, color='tab:blue', alpha=0.3)  # Add connecting line
                ax1.set_xlabel('Місяць')
                ax1.set_ylabel('Відсоток успішних замовлень (%)', color='tab:blue')
                ax1.tick_params(axis='y', labelcolor='tab:blue')

                # Show only every 6th month label
                n_months = len(months)
                plt.xticks(range(0, n_months, 6), [months[i] for i in range(0, n_months, 6)], rotation=45, ha='right')

                # Create second y-axis for total orders
                ax2 = ax1.twinx()
                line = ax2.plot(months, total_orders, color='tab:orange', linewidth=2, label='Кількість замовлень')
                ax2.set_ylabel('Загальна кількість замовлень', color='tab:orange')
                ax2.tick_params(axis='y', labelcolor='tab:orange')

                # Add value labels for each point
                for i, (x, y, orders) in enumerate(zip(months, success_rates, total_orders)):
                    ax1.annotate(
                        f"{y:.1f}%",
                        (x, y),
                        xytext=(0, 10),
                        textcoords='offset points',
                        ha='center',
                        va='bottom'
                    )

                plt.title('Щомісячний відсоток успішних замовлень')
                plt.grid(True, linestyle='--', alpha=0.7)

                # Adjust layout to prevent label cutoff
                plt.tight_layout()

                # Save the chart
                buffer = BytesIO()
                plt.savefig(buffer, format='png', bbox_inches='tight',
                            dpi=100, pad_inches=0.2)
                plt.close()

                record.monthly_success_rate_chart = base64.b64encode(buffer.getvalue())

            except Exception as e:
                print(f"Error computing monthly success rate chart: {str(e)}")
                record.monthly_success_rate_chart = False
                plt.close('all')

    def _compute_monthly_volume_success_chart(self):
        """Compute chart showing success rate by monthly order volume"""
        for record in self:
            if not record.data_file:
                record.monthly_volume_success_chart = False
                continue

            try:
                # Read CSV data
                data = record._read_csv_data()
                if not data:
                    continue

                # Group orders by month
                monthly_stats = defaultdict(lambda: {'total': 0, 'success': 0})

                # Collect statistics for each month
                for row in data:
                    order_date = row['date_order']
                    month_key = order_date.strftime('%Y-%m')

                    monthly_stats[month_key]['total'] += 1
                    if row['state'] == 'sale':
                        monthly_stats[month_key]['success'] += 1

                if not monthly_stats:
                    print("No data to plot")
                    record.monthly_volume_success_chart = False
                    continue

                # Calculate success rate for each month and prepare data for plotting
                plot_data = []
                for month, stats in monthly_stats.items():
                    if stats['total'] > 0:
                        success_rate = (stats['success'] / stats['total'] * 100)
                        plot_data.append({
                            'month': month,
                            'success_rate': success_rate,
                            'total_orders': stats['total']
                        })

                # Sort by total orders
                plot_data.sort(key=lambda x: x['total_orders'])

                # Group months into 20 equal groups by success rate
                num_months = len(plot_data)
                months_per_group = max(1, num_months // 20)
                remainder = num_months % 20

                grouped_data = []
                start_idx = 0

                for i in range(20):
                    # Add one extra month to first 'remainder' groups
                    current_group_size = months_per_group + (1 if i < remainder else 0)
                    if current_group_size == 0:
                        break

                    end_idx = start_idx + current_group_size
                    group = plot_data[start_idx:end_idx]

                    if group:
                        avg_success_rate = sum(m['success_rate'] for m in group) / len(group)
                        avg_orders = sum(m['total_orders'] for m in group) / len(group)
                        months_in_group = [m['month'] for m in group]

                        grouped_data.append({
                            'success_rate': avg_success_rate,
                            'avg_orders': avg_orders,
                            'months': months_in_group,
                            'months_count': len(group)
                        })

                    start_idx = end_idx

                # Create the chart
                plt.figure(figsize=(12, 8))

                # Extract data for plotting
                success_rates = [d['success_rate'] for d in grouped_data]
                avg_orders = [d['avg_orders'] for d in grouped_data]
                months_counts = [d['months_count'] for d in grouped_data]

                # Create scatter plot
                plt.scatter(avg_orders, success_rates, s=100, alpha=0.6)
                print(f"_compute_monthly_volume_success_chart avg_orders = {avg_orders}")
                print(f"_compute_monthly_volume_success_chart success_rates = {success_rates}")

                # Add trend line
                z = np.polyfit(avg_orders, success_rates, 1)
                p = np.poly1d(z)
                plt.plot(avg_orders, p(avg_orders), "r--", alpha=0.8)

                # Calculate average months per point
                avg_months_per_point = sum(months_counts) / len(months_counts)

                plt.xlabel('Середня кількість замовлень за місяць')
                plt.ylabel('Середній відсоток успішних замовлень (%)')
                plt.title(f'Залежність успішності від середньомісячної кількості замовлень\n'
                          f'(в середньому {avg_months_per_point:.1f} місяців на точку, '
                          f'всього {sum(months_counts)} місяців)')
                plt.grid(True, linestyle='--', alpha=0.7)

                # Save the chart
                buffer = BytesIO()
                plt.savefig(buffer, format='png', bbox_inches='tight',
                            dpi=100, pad_inches=0.2)
                plt.close()

                record.monthly_volume_success_chart = base64.b64encode(buffer.getvalue())

            except Exception as e:
                print(f"Error computing monthly volume success chart: {str(e)}")
                record.monthly_volume_success_chart = False
                plt.close('all')

    def _compute_monthly_orders_success_chart(self):
        """Compute chart showing success rate by monthly orders count"""
        for record in self:
            if not record.data_file:
                record.monthly_orders_success_chart = False
                continue

            try:
                # Read CSV data
                data = record._read_csv_data()
                if not data:
                    continue

                # Group orders by month
                monthly_stats = defaultdict(lambda: {'total': 0, 'success': 0})

                # Collect statistics for each month
                for row in data:
                    order_date = row['date_order']
                    month_key = order_date.strftime('%Y-%m')

                    monthly_stats[month_key]['total'] += 1
                    if row['state'] == 'sale':
                        monthly_stats[month_key]['success'] += 1

                if not monthly_stats:
                    print("No data to plot")
                    record.monthly_orders_success_chart = False
                    continue

                # Calculate success rate for each month and prepare data for plotting
                plot_data = []
                for month, stats in monthly_stats.items():
                    if stats['total'] > 0:
                        success_rate = (stats['success'] / stats['total'] * 100)
                        plot_data.append({
                            'month': month,
                            'success_rate': success_rate,
                            'total_orders': stats['total']
                        })

                # Sort by total orders
                plot_data.sort(key=lambda x: x['total_orders'])

                # Find min and max order counts
                min_orders = min(m['total_orders'] for m in plot_data)
                max_orders = max(m['total_orders'] for m in plot_data)

                # Create 20 equal ranges of order counts
                range_size = (max_orders - min_orders) / 20

                # Initialize groups
                groups = [[] for _ in range(20)]

                # Distribute months into groups based on order count ranges
                for month_data in plot_data:
                    if range_size > 0:
                        # Визначаємо індекс групи на основі кількості замовлень
                        group_index = min(19, int((month_data['total_orders'] - min_orders) / range_size))
                    else:
                        group_index = 0
                    groups[group_index].append(month_data)

                # Calculate statistics for each group
                grouped_data = []
                for i, group in enumerate(groups):
                    if group:  # Only process non-empty groups
                        avg_success_rate = sum(m['success_rate'] for m in group) / len(group)
                        avg_orders = sum(m['total_orders'] for m in group) / len(group)

                        grouped_data.append({
                            'success_rate': avg_success_rate,
                            'avg_orders': avg_orders,
                            'months_count': len(group),
                            'min_orders': min(m['total_orders'] for m in group),
                            'max_orders': max(m['total_orders'] for m in group)
                        })

                # Sort by average orders for plotting
                grouped_data.sort(key=lambda x: x['avg_orders'])

                print("\n_compute_monthly_orders_success_chart ranges:")
                for i, group in enumerate(grouped_data):
                    print(
                        f"Group {i}: {group['min_orders']}-{group['max_orders']} orders, {group['months_count']} months")

                # Create the chart
                plt.figure(figsize=(12, 8))

                # Extract data for plotting
                success_rates = [d['success_rate'] for d in grouped_data]
                avg_orders = [d['avg_orders'] for d in grouped_data]
                months_counts = [d['months_count'] for d in grouped_data]

                # Create scatter plot
                plt.scatter(avg_orders, success_rates, s=100, alpha=0.6)
                print(f"_compute_monthly_orders_success_chart avg_orders = {avg_orders}")
                print(f"_compute_monthly_orders_success_chart success_rates = {success_rates}")

                # Add trend line
                z = np.polyfit(avg_orders, success_rates, 1)
                p = np.poly1d(z)
                plt.plot(avg_orders, p(avg_orders), "r--", alpha=0.8)

                # Calculate average months per point
                avg_months_per_point = sum(months_counts) / len(months_counts)

                plt.xlabel('Середня кількість замовлень за місяць')
                plt.ylabel('Середній відсоток успішних замовлень (%)')
                plt.title(f'Залежність успішності від кількості замовлень\n'
                          f'(діапазон замовлень: {min_orders:.0f}-{max_orders:.0f}, '
                          f'всього {sum(months_counts)} місяців)')
                plt.grid(True, linestyle='--', alpha=0.7)

                # Save the chart
                buffer = BytesIO()
                plt.savefig(buffer, format='png', bbox_inches='tight',
                            dpi=100, pad_inches=0.2)
                plt.close()

                record.monthly_orders_success_chart = base64.b64encode(buffer.getvalue())

            except Exception as e:
                print(f"Error computing monthly orders success chart: {str(e)}")
                record.monthly_orders_success_chart = False
                plt.close('all')

    def _compute_payment_term_success_chart(self):
        """Compute chart showing success rate by payment terms"""
        for record in self:
            if not record.data_file:
                record.payment_term_success_chart = False
                continue

            try:
                # Read CSV data
                data = record._read_csv_data()
                if not data:
                    continue

                # Get payment terms names
                payment_terms = {
                    str(pt.id): pt.name
                    for pt in self.env['account.payment.term'].search([])
                }
                payment_terms['Not specified'] = 'Не вказано'
                payment_terms['False'] = 'Не вказано'

                # Group orders by payment term
                payment_term_stats = defaultdict(lambda: {'total': 0, 'success': 0, 'name': 'Не вказано'})

                # Collect statistics for each payment term
                for row in data:
                    payment_term_id = row.get('payment_term_id')
                    if not payment_term_id or payment_term_id == 'False':
                        payment_term_id = 'Not specified'

                    payment_term_stats[payment_term_id]['total'] += 1
                    payment_term_stats[payment_term_id]['name'] = payment_terms.get(str(payment_term_id), 'Не вказано')
                    if row['state'] == 'sale':
                        payment_term_stats[payment_term_id]['success'] += 1

                if not payment_term_stats:
                    print("No data to plot")
                    record.payment_term_success_chart = False
                    continue

                # Calculate success rate for each payment term
                plot_data = []
                for term_id, stats in payment_term_stats.items():
                    if stats['total'] > 0:
                        success_rate = (stats['success'] / stats['total'] * 100)
                        plot_data.append({
                            'term_id': term_id,
                            'name': stats['name'],
                            'success_rate': success_rate,
                            'total_orders': stats['total']
                        })

                # Sort by success rate
                plot_data.sort(key=lambda x: x['success_rate'])

                # Create the chart
                plt.figure(figsize=(15, 10))

                # Extract data for plotting
                term_names = [f"{d['name']}\n(ID: {d['term_id']})" for d in plot_data]
                success_rates = [d['success_rate'] for d in plot_data]
                total_orders = [d['total_orders'] for d in plot_data]

                # Create bar chart with custom colors based on success rate
                colors = ['#ff4d4d' if rate < 50 else '#00cc00' for rate in success_rates]
                bars = plt.bar(term_names, success_rates, color=colors, alpha=0.6)

                # Add value labels
                for i, (bar, orders) in enumerate(zip(bars, total_orders)):
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2, height,
                             f'{orders}',
                             ha='center', va='bottom')

                plt.xlabel('Умови оплати')
                plt.ylabel('Відсоток успішних замовлень (%)')
                plt.title('Залежність успішності від умов оплати\n(числа показують кількість замовлень)')
                plt.grid(True, linestyle='--', alpha=0.7)
                plt.xticks(rotation=90, ha='right')

                # Adjust layout to prevent label cutoff
                plt.tight_layout()

                # Save the chart
                buffer = BytesIO()
                plt.savefig(buffer, format='png', bbox_inches='tight',
                            dpi=100, pad_inches=0.2)
                plt.close()

                record.payment_term_success_chart = base64.b64encode(buffer.getvalue())

            except Exception as e:
                print(f"Error computing payment term success chart: {str(e)}")
                record.payment_term_success_chart = False
                plt.close('all')

    @api.depends('data_file')
    def _compute_monthly_scatter_charts(self):
        for record in self:
            if not record.data_file:
                record.monthly_analysis_scatter_chart = False
                continue

            try:
                # Read CSV data
                csv_data = base64.b64decode(record.data_file)
                csv_file = StringIO(csv_data.decode('utf-8'))
                reader = csv.DictReader(csv_file)

                # Prepare monthly data
                monthly_data = {}
                for row in reader:
                    date = datetime.strptime(row['date_order'].split()[0], '%Y-%m-%d')
                    month_key = date.strftime('%m/%Y')

                    if month_key not in monthly_data:
                        monthly_data[month_key] = {
                            'orders': 0,
                            'successful': 0,
                            'rate': 0
                        }

                    monthly_data[month_key]['orders'] += 1
                    if row['state'] == 'sale':
                        monthly_data[month_key]['successful'] += 1

                print(f"MONTHLY_DATA: {monthly_data}")
                # Calculate success rates
                for month in monthly_data:
                    total = monthly_data[month]['orders']
                    successful = monthly_data[month]['successful']
                    monthly_data[month]['rate'] = (successful / total * 100) if total > 0 else 0

                # Sort months chronologically
                sorted_months = sorted(monthly_data.keys(),
                                       key=lambda x: datetime.strptime(x, '%m/%Y'))

                # Create data arrays in chronological order
                months = sorted_months
                orders_data = [monthly_data[month]['orders'] for month in months]
                successful_data = [monthly_data[month]['successful'] for month in months]
                rate_data = [monthly_data[month]['rate'] for month in months]

                if not months:
                    record.monthly_analysis_scatter_chart = False
                    continue

                # Create monthly scatter chart
                fig, ax1 = plt.subplots(figsize=(15, 8))

                # Створюємо другу вісь Y
                ax2 = ax1.twinx()

                # Підготовка даних для осі X
                x = np.arange(len(months))
                months_display = [datetime.strptime(m, '%m/%Y').strftime('%B %Y') for m in months]
                ax1.set_xticks(x)
                ax1.set_xticklabels(months_display, rotation=90, ha='center')

                # Графіки для кількості замовлень (ліва вісь) - тільки точки, без ліній
                scatter1 = ax1.scatter(x, orders_data, color='skyblue', s=100, label='Total Orders')
                scatter2 = ax1.scatter(x, successful_data, color='gold', s=100, label='Successful Orders')

                # Графік для відсотків (права вісь) - тільки точки, без ліній
                scatter3 = ax2.scatter(x, rate_data, color='purple', s=100, label='Success Rate (%)')

                # Налаштування лівої осі (кількість)
                ax1.set_xlabel('Month')
                ax1.set_ylabel('Count')
                ax1.tick_params(axis='y', labelcolor='black')

                # Налаштування правої осі (відсотки)
                ax2.set_ylabel('Success Rate (%)')
                ax2.tick_params(axis='y', labelcolor='purple')

                # Об'єднуємо легенди з обох осей
                handles = [scatter1, scatter2, scatter3]
                labels = ['Total Orders', 'Successful Orders', 'Success Rate (%)']
                ax1.legend(handles, labels, loc='upper left')

                plt.title('Monthly Orders Analysis (Scatter)')
                plt.grid(True)
                plt.subplots_adjust(bottom=0.2)
                plt.tight_layout()

                # Save chart
                buffer = BytesIO()
                plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
                plt.close()
                record.monthly_analysis_scatter_chart = base64.b64encode(buffer.getvalue())
                print(f"Chart: {record.monthly_analysis_scatter_chart}")

            except Exception as e:
                print(f'Error computing monthly scatter charts: {e.__class__}: {e}')
                record.monthly_analysis_scatter_chart = False
                continue
            finally:
                plt.close('all')

    def action_compute_and_draw(self):
        self._compute_monthly_combined_chart()
        self._compute_relative_age_success_chart()

    def _compute_monthly_combined_chart(self):
        """Compute combined monthly chart with orders count, success rate and relative customer age"""
        print("\n=== Computing Monthly Combined Chart ===")

        if not self.data_file:
            return

        try:
            data = self._read_csv_data()
            if not data:
                return

            # Find the earliest date (date_from) from the data
            date_from = min(row['date_order'] for row in data)

            # Group data by months
            monthly_data = defaultdict(lambda: {
                'total_orders': 0,
                'successful_orders': 0,
                'customer_ages': []
            })

            for row in data:
                order_date = row['date_order']
                month_key = order_date.strftime('%Y-%m')

                # Count orders
                monthly_data[month_key]['total_orders'] += 1

                # Count successful orders (assuming 'done' or 'sale' are success states)
                if row['state'] in ['done', 'sale']:
                    monthly_data[month_key]['successful_orders'] += 1

                # Calculate relative customer age
                customer_since = row['partner_create_date']
                total_time = (order_date - date_from).days / 30.0  # Total time in months
                customer_age = (order_date - customer_since).days / 30.0  # Age in months
                relative_age = (customer_age / total_time * 100) if total_time > 0 else 0
                monthly_data[month_key]['customer_ages'].append(relative_age)

            # Sort months
            sorted_months = sorted(monthly_data.keys())

            # Prepare data for plotting
            months = []
            orders_count = []
            success_rates = []
            avg_relative_ages = []

            for month in sorted_months:
                data = monthly_data[month]
                total = data['total_orders']
                successful = data['successful_orders']
                ages = data['customer_ages']

                months.append(datetime.strptime(month, '%Y-%m'))
                orders_count.append(total)
                success_rates.append((successful / total * 100) if total > 0 else 0)
                avg_relative_ages.append(sum(ages) / len(ages) if ages else 0)

            # Create figure and primary axis
            fig, ax1 = plt.subplots(figsize=(15, 8))

            # Primary axis - Total Orders (blue)
            color1 = 'blue'
            ax1.set_xlabel('Month')
            ax1.set_ylabel('Total Orders', color=color1)
            ax1.plot(months, orders_count, color=color1, marker='.', markersize=10, label='Total Orders')
            ax1.tick_params(axis='y', labelcolor=color1)

            # Secondary axis - Success Rate (orange)
            ax2 = ax1.twinx()
            color2 = 'orange'
            ax2.set_ylabel('Success Rate (%)', color=color2)
            ax2.plot(months, success_rates, color=color2, marker='.', markersize=10, label='Success Rate (%)')
            ax2.tick_params(axis='y', labelcolor=color2)

            # Third axis - Relative Customer Age (green)
            ax3 = ax1.twinx()
            # Offset the third axis
            ax3.spines["right"].set_position(("axes", 1.1))
            color3 = 'green'
            ax3.set_ylabel('Relative Customer Age (%)', color=color3)
            ax3.plot(months, avg_relative_ages, color=color3, marker='.', markersize=10,
                     label='Relative Customer Age (%)\n(% of time from first order)')
            ax3.tick_params(axis='y', labelcolor=color3)

            # Format x-axis
            ax1.xaxis.set_major_locator(plt.matplotlib.dates.MonthLocator(interval=6))
            ax1.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m'))
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

            # Add legend with explanation
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            lines3, labels3 = ax3.get_legend_handles_labels()
            ax3.legend(lines1 + lines2 + lines3, labels1 + labels2 + labels3,
                       loc='upper right', bbox_to_anchor=(1.2, 1.0))

            plt.title(
                'Monthly Combined Analysis\nRelative Customer Age shows the average customer age as a percentage of time passed since first order')
            plt.grid(True)
            plt.tight_layout()

            # Save to binary field
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight')
            plt.close()
            self.monthly_combined_chart = base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error computing monthly combined chart: {str(e)}")
            return

    def _compute_relative_age_success_chart(self):
        """Compute chart showing relationship between success rate and absolute customer age (in months),
        grouped into intervals by success rate with subgroups for large groups"""
        print("\n=== Computing Success Rate vs Customer Age Chart ===")

        if not self.data_file:
            return

        try:
            data = self._read_csv_data()
            if not data:
                return

            # Get current date for age calculation
            current_date = max(row['date_order'] for row in data)

            # Calculate success rate and age for each partner
            partner_data = defaultdict(lambda: {
                'total_orders': 0,
                'successful_orders': 0,
                'customer_since': None,
                'success_rate': 0
            })

            # Collect data for each partner
            for row in data:
                partner_id = row['partner_id']
                partner_data[partner_id]['total_orders'] += 1
                if row['state'] in ['done', 'sale']:
                    partner_data[partner_id]['successful_orders'] += 1
                partner_data[partner_id]['customer_since'] = row['partner_create_date']

            # Calculate success rate and age for each partner
            for partner_id, data in partner_data.items():
                success_rate = (data['successful_orders'] / data['total_orders'] * 100) if data[
                                                                                               'total_orders'] > 0 else 0
                partner_data[partner_id]['success_rate'] = success_rate
                # Calculate age in months
                age_days = (current_date - data['customer_since']).days
                partner_data[partner_id]['age_months'] = age_days / 30.0

            # Create initial 20 groups (0-5%, 5-10%, etc.)
            initial_groups = defaultdict(list)

            # Distribute partners into initial groups
            for partner_id, data in partner_data.items():
                success_rate = data['success_rate']
                group_index = min(int(success_rate // 5), 19)  # 20 groups (0-19)
                initial_groups[group_index].append({
                    'partner_id': partner_id,
                    'success_rate': data['success_rate'],
                    'age_months': data['age_months']
                })

            # Process groups and split if necessary
            plot_data = []
            for group_index, partners in initial_groups.items():
                if len(partners) > 500:
                    # Sort partners by success rate for even distribution
                    partners.sort(key=lambda x: x['success_rate'])
                    # Calculate number of subgroups needed
                    num_subgroups = (len(partners) + 499) // 500  # Round up division
                    subgroup_size = len(partners) // num_subgroups
                    remainder = len(partners) % num_subgroups

                    # Create subgroups
                    start_idx = 0
                    for i in range(num_subgroups):
                        current_size = subgroup_size + (1 if i < remainder else 0)
                        subgroup = partners[start_idx:start_idx + current_size]

                        avg_success_rate = sum(p['success_rate'] for p in subgroup) / len(subgroup)
                        avg_age = sum(p['age_months'] for p in subgroup) / len(subgroup)

                        plot_data.append({
                            'success_rate': avg_success_rate,
                            'avg_age': avg_age,
                            'partners_count': len(subgroup)
                        })

                        start_idx += current_size
                else:
                    # Process regular group
                    success_rate_mid = group_index * 5 + 2.5
                    avg_age = sum(p['age_months'] for p in partners) / len(partners)
                    plot_data.append({
                        'success_rate': success_rate_mid,
                        'avg_age': avg_age,
                        'partners_count': len(partners)
                    })

            # Sort plot data by success rate for consistent visualization
            plot_data.sort(key=lambda x: x['success_rate'])

            # Prepare data for plotting
            success_rates = [d['success_rate'] for d in plot_data]
            avg_ages = [d['avg_age'] for d in plot_data]
            partners_counts = [d['partners_count'] for d in plot_data]

            # Calculate marker sizes (scaled for better visibility)
            max_count = max(partners_counts)
            marker_sizes = [100 + (count / max_count) * 900 for count in partners_counts]

            # Create plot
            plt.figure(figsize=(15, 8))
            scatter = plt.scatter(success_rates, avg_ages, s=marker_sizes, alpha=0.6)

            # Add count labels next to points
            for i, (x, y, count) in enumerate(zip(success_rates, avg_ages, partners_counts)):
                plt.annotate(f'  {count}', (x, y),
                             xytext=(5, 5), textcoords='offset points')

            plt.xlabel('Success Rate (%)')
            plt.ylabel('Average Customer Age (months)')
            plt.title(
                'Average Customer Age by Success Rate Intervals\nGroups with >500 customers are subdivided by success rate\nBubble size and number indicate customer count in each group')

            # Set x-axis ticks
            plt.xticks([i * 5 for i in range(21)],
                       [f'{i * 5}' for i in range(21)],
                       rotation=45)

            plt.grid(True)
            plt.tight_layout()

            # Save to binary field
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight')
            plt.close()
            self.relative_age_success_chart = base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error computing success rate vs customer age chart: {str(e)}")
            return



    def _compute_salesperson_age_success_chart(self):
        """Compute chart showing success rate by salesperson age"""
        print("\nComputing salesperson age success chart...")

        try:
            # Читаємо дані з CSV
            data = self._read_csv_data()
            if not data:
                return

            # Групуємо замовлення по менеджерам
            salesperson_data = defaultdict(lambda: {
                'first_order_date': None,
                'last_order_date': None,
                'total_orders': 0,
                'successful_orders': 0
            })

            # Збираємо дані по кожному менеджеру
            for row in data:
                user_id = row['user_id']
                if not user_id:
                    continue

                order_date = row['date_order']

                # Оновлюємо першу та останню дату замовлення
                if not salesperson_data[user_id]['first_order_date'] or order_date < salesperson_data[user_id][
                    'first_order_date']:
                    salesperson_data[user_id]['first_order_date'] = order_date
                if not salesperson_data[user_id]['last_order_date'] or order_date > salesperson_data[user_id][
                    'last_order_date']:
                    salesperson_data[user_id]['last_order_date'] = order_date

                # Рахуємо замовлення
                salesperson_data[user_id]['total_orders'] += 1
                if row['state'] in ['done', 'sale']:
                    salesperson_data[user_id]['successful_orders'] += 1

            # Розраховуємо вік та успішність для кожного менеджера
            chart_data = []
            for user_id, data in salesperson_data.items():
                # Пропускаємо менеджерів з малою кількістю замовлень
                if data['total_orders'] < 5:
                    continue

                # Вік в місяцях
                age_days = (data['last_order_date'] - data['first_order_date']).days
                age_months = age_days / 30.0

                # Відсоток успішних замовлень
                success_rate = (data['successful_orders'] / data['total_orders'] * 100)

                chart_data.append({
                    'age_months': age_months,
                    'success_rate': success_rate,
                    'total_orders': data['total_orders']
                })

            # Створюємо графік
            plt.figure(figsize=(15, 8))

            # Малюємо точки однакового розміру
            plt.scatter([d['age_months'] for d in chart_data],
                        [d['success_rate'] for d in chart_data],
                        s=100, alpha=0.5)

            # Додаємо мітки з кількістю замовлень біля кожної точки
            for d in chart_data:
                plt.annotate(str(d['total_orders']),
                             (d['age_months'], d['success_rate']),
                             xytext=(5, 5), textcoords='offset points')

            plt.xlabel('Salesperson Age (Months)')
            plt.ylabel('Success Rate (%)')
            plt.title('Success Rate by Salesperson Age')

            # Додаємо сітку
            plt.grid(True, linestyle='--', alpha=0.7)

            # Зберігаємо графік
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            plt.close()

            # Конвертуємо в base64
            self.salesperson_age_success_chart = base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error computing salesperson age success chart: {str(e)}")

    def _compute_salesperson_orders_success_chart(self):
        """Compute chart showing success rate by total number of salesperson orders"""
        print("\nComputing salesperson orders success chart...")

        try:
            # Читаємо дані з CSV
            data = self._read_csv_data()
            if not data:
                return

            # Групуємо замовлення по менеджерам
            salesperson_data = defaultdict(lambda: {
                'total_orders': 0,
                'successful_orders': 0
            })

            # Збираємо дані по кожному менеджеру
            for row in data:
                user_id = row['user_id']
                if not user_id:
                    continue

                # Рахуємо замовлення
                salesperson_data[user_id]['total_orders'] += 1
                if row['state'] in ['done', 'sale']:
                    salesperson_data[user_id]['successful_orders'] += 1

            # Розраховуємо успішність для кожного менеджера
            chart_data = []
            for user_id, data in salesperson_data.items():
                # Пропускаємо менеджерів з малою кількістю замовлень
                if data['total_orders'] < 5:
                    continue

                # Відсоток успішних замовлень
                success_rate = (data['successful_orders'] / data['total_orders'] * 100)

                chart_data.append({
                    'total_orders': data['total_orders'],
                    'success_rate': success_rate
                })

            # Створюємо графік
            plt.figure(figsize=(15, 8))

            # Малюємо точки
            plt.scatter([d['total_orders'] for d in chart_data],
                        [d['success_rate'] for d in chart_data],
                        s=100, alpha=0.5)

            # Додаємо мітки з ID менеджера біля кожної точки
            for d in chart_data:
                plt.annotate(str(d['total_orders']),
                             (d['total_orders'], d['success_rate']),
                             xytext=(5, 5), textcoords='offset points')

            plt.xlabel('Total Number of Orders')
            plt.ylabel('Success Rate (%)')
            plt.title('Success Rate by Total Number of Salesperson Orders')

            # Додаємо сітку
            plt.grid(True, linestyle='--', alpha=0.7)

            # Зберігаємо графік
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            plt.close()

            # Конвертуємо в base64
            self.salesperson_orders_success_chart = base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error computing salesperson orders success chart: {str(e)}")

    def _compute_salesperson_total_amount_success_chart(self):
        """Compute chart showing success rate by total amount of salesperson orders"""
        try:
            # Читаємо дані з CSV
            data = self._read_csv_data()
            if not data:
                return

            # Групуємо замовлення по менеджерам
            salesperson_data = defaultdict(lambda: {
                'total_orders': 0,
                'successful_orders': 0,
                'total_amount': 0.0
            })

            # Збираємо дані по кожному менеджеру
            for row in data:
                user_id = row['user_id']
                if not user_id:
                    continue

                amount = float(row['amount_total'])

                # Рахуємо замовлення та суми ВСІХ замовлень
                salesperson_data[user_id]['total_orders'] += 1
                salesperson_data[user_id]['total_amount'] += amount  # Додаємо суму до загальної
                if row['state'] in ['done', 'sale']:
                    salesperson_data[user_id]['successful_orders'] += 1

            # Створюємо лог перед побудовою графіка
            log_message = "\nTotal Amount Chart - Final Data:\n"
            for user_id, data in salesperson_data.items():
                if data['total_orders'] >= 5:
                    success_rate = (data['successful_orders'] / data['total_orders'] * 100)
                    log_message += (
                        f"Salesperson {user_id}:\n"
                        f"  - Total Orders: {data['total_orders']}\n"
                        f"  - Successful Orders: {data['successful_orders']}\n"
                        f"  - Total Amount: {data['total_amount']:.2f}\n"
                        f"  - Success Rate: {success_rate:.2f}%\n"
                    )

            # Розраховуємо успішність для кожного менеджера
            chart_data = []
            for user_id, data in salesperson_data.items():
                # Пропускаємо менеджерів з малою кількістю замовлень
                if data['total_orders'] < 5:
                    continue

                # Відсоток успішних замовлень
                success_rate = (data['successful_orders'] / data['total_orders'] * 100)

                chart_data.append({
                    'total_amount': data['total_amount'],
                    'success_rate': success_rate,
                    'total_orders': data['total_orders']
                })

            plt.clf()
            # Створюємо графік
            plt.figure(figsize=(15, 8))

            # Малюємо точки
            plt.scatter([d['total_amount'] for d in chart_data],
                        [d['success_rate'] for d in chart_data],
                        s=100, alpha=0.5)

            # Додаємо мітки з кількістю замовлень біля кожної точки
            for d in chart_data:
                plt.annotate(str(d['total_orders']),
                             (d['total_amount'], d['success_rate']),
                             xytext=(5, 5), textcoords='offset points')

            plt.xlabel('Total Amount of All Orders')
            plt.ylabel('Success Rate (%)')
            plt.title('Success Rate by Total Amount of All Salesperson Orders')

            # Форматуємо вісь X для відображення сум у тисячах
            ax = plt.gca()
            ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x / 1000), ',')))
            plt.xlabel('Total Amount of All Orders (Thousands)')

            # Додаємо сітку
            plt.grid(True, linestyle='--', alpha=0.7)

            # Зберігаємо графік
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            plt.close()

            # Конвертуємо в base64
            self.salesperson_total_amount_success_chart = base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error computing salesperson total amount success chart: {str(e)}")

    def _compute_salesperson_success_amount_success_chart(self):
        """Compute chart showing success rate by amount of successful salesperson orders"""
        try:
            # Читаємо дані з CSV
            data = self._read_csv_data()
            if not data:
                return

            # Групуємо замовлення по менеджерам
            salesperson_data = defaultdict(lambda: {
                'total_orders': 0,
                'successful_orders': 0,
                'success_amount': 0.0
            })

            # Збираємо дані по кожному менеджеру
            for row in data:
                user_id = row['user_id']
                if not user_id:
                    continue

                amount = float(row['amount_total'])

                # Рахуємо замовлення та суми тільки УСПІШНИХ замовлень
                salesperson_data[user_id]['total_orders'] += 1
                if row['state'] in ['done', 'sale']:
                    salesperson_data[user_id]['successful_orders'] += 1
                    salesperson_data[user_id]['success_amount'] += amount  # Додаємо суму тільки для успішних

            # Створюємо лог перед побудовою графіка
            log_message = "\nSuccess Amount Chart - Final Data:\n"
            for user_id, data in salesperson_data.items():
                if data['total_orders'] >= 5:
                    success_rate = (data['successful_orders'] / data['total_orders'] * 100)
                    log_message += (
                        f"Salesperson {user_id}:\n"
                        f"  - Total Orders: {data['total_orders']}\n"
                        f"  - Successful Orders: {data['successful_orders']}\n"
                        f"  - Success Amount: {data['success_amount']:.2f}\n"
                        f"  - Success Rate: {success_rate:.2f}%\n"
                    )

            # Розраховуємо успішність для кожного менеджера
            chart_data = []
            for user_id, data in salesperson_data.items():
                # Пропускаємо менеджерів з малою кількістю замовлень
                if data['total_orders'] < 5:
                    continue

                # Відсоток успішних замовлень
                success_rate = (data['successful_orders'] / data['total_orders'] * 100)

                chart_data.append({
                    'success_amount': data['success_amount'],
                    'success_rate': success_rate,
                    'total_orders': data['total_orders']
                })

            plt.clf()
            # Створюємо графік
            plt.figure(figsize=(15, 8))

            # Малюємо точки
            plt.scatter([d['success_amount'] for d in chart_data],
                        [d['success_rate'] for d in chart_data],
                        s=100, alpha=0.5)

            # Додаємо мітки з кількістю замовлень біля кожної точки
            for d in chart_data:
                plt.annotate(str(d['total_orders']),
                             (d['success_amount'], d['success_rate']),
                             xytext=(5, 5), textcoords='offset points')

            plt.xlabel('Amount of Successful Orders Only')
            plt.ylabel('Success Rate (%)')
            plt.title('Success Rate by Amount of Successful Salesperson Orders')

            # Форматуємо вісь X для відображення сум у тисячах
            ax = plt.gca()
            ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x / 1000), ',')))
            plt.xlabel('Amount of Successful Orders Only (Thousands)')

            # Додаємо сітку
            plt.grid(True, linestyle='--', alpha=0.7)

            # Зберігаємо графік
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            plt.close()

            # Конвертуємо в base64
            self.salesperson_success_amount_success_chart = base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error computing salesperson success amount success chart: {str(e)}")

    def _compute_salesperson_avg_amount_success_chart(self):
        """Compute chart showing success rate by average amount of all salesperson orders"""
        try:
            # Читаємо дані з CSV
            data = self._read_csv_data()
            if not data:
                return

            # Групуємо замовлення по менеджерам
            salesperson_data = defaultdict(lambda: {
                'total_orders': 0,
                'successful_orders': 0,
                'total_amount': 0.0
            })

            # Збираємо дані по кожному менеджеру
            for row in data:
                user_id = row['user_id']
                if not user_id:
                    continue

                amount = float(row['amount_total'])

                # Рахуємо замовлення та суми ВСІХ замовлень
                salesperson_data[user_id]['total_orders'] += 1
                salesperson_data[user_id]['total_amount'] += amount
                if row['state'] in ['done', 'sale']:
                    salesperson_data[user_id]['successful_orders'] += 1

            # Створюємо лог перед побудовою графіка
            log_message = "\nAverage Amount Chart - Final Data:\n"
            chart_data = []
            for user_id, data in salesperson_data.items():
                if data['total_orders'] >= 5:
                    success_rate = (data['successful_orders'] / data['total_orders'] * 100)
                    avg_amount = data['total_amount'] / data['total_orders']

                    log_message += (
                        f"Salesperson {user_id}:\n"
                        f"  - Total Orders: {data['total_orders']}\n"
                        f"  - Successful Orders: {data['successful_orders']}\n"
                        f"  - Average Amount: {avg_amount:.2f}\n"
                        f"  - Success Rate: {success_rate:.2f}%\n"
                    )

                    chart_data.append({
                        'avg_amount': avg_amount,
                        'success_rate': success_rate,
                        'total_orders': data['total_orders']
                    })

            # Очищаємо попередній графік
            plt.clf()

            # Створюємо графік
            plt.figure(figsize=(15, 8))

            # Малюємо точки
            plt.scatter([d['avg_amount'] for d in chart_data],
                        [d['success_rate'] for d in chart_data],
                        s=100, alpha=0.5)

            # Додаємо мітки з кількістю замовлень біля кожної точки
            for d in chart_data:
                plt.annotate(str(d['total_orders']),
                             (d['avg_amount'], d['success_rate']),
                             xytext=(5, 5), textcoords='offset points')

            plt.xlabel('Average Amount of All Orders')
            plt.ylabel('Success Rate (%)')
            plt.title('Success Rate by Average Amount of All Salesperson Orders')

            # Форматуємо вісь X для відображення сум у тисячах
            ax = plt.gca()
            ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x / 1000), ',')))
            plt.xlabel('Average Amount of All Orders (Thousands)')

            # Додаємо сітку
            plt.grid(True, linestyle='--', alpha=0.7)

            # Зберігаємо графік
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            plt.close()

            # Конвертуємо в base64
            self.salesperson_avg_amount_success_chart = base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error computing salesperson average amount success chart: {str(e)}")

    def _compute_salesperson_avg_success_amount_success_chart(self):
        """Compute chart showing success rate by average amount of successful salesperson orders"""
        try:
            # Читаємо дані з CSV
            data = self._read_csv_data()
            if not data:
                return

            # Групуємо замовлення по менеджерам
            salesperson_data = defaultdict(lambda: {
                'total_orders': 0,
                'successful_orders': 0,
                'success_amount': 0.0
            })

            # Збираємо дані по кожному менеджеру
            for row in data:
                user_id = row['user_id']
                if not user_id:
                    continue

                amount = float(row['amount_total'])

                # Рахуємо замовлення та суми тільки УСПІШНИХ замовлень
                salesperson_data[user_id]['total_orders'] += 1
                if row['state'] in ['done', 'sale']:
                    salesperson_data[user_id]['successful_orders'] += 1
                    salesperson_data[user_id]['success_amount'] += amount

            # Створюємо лог перед побудовою графіка
            log_message = "\nAverage Success Amount Chart - Final Data:\n"
            chart_data = []
            for user_id, data in salesperson_data.items():
                if data['total_orders'] >= 5:
                    success_rate = (data['successful_orders'] / data['total_orders'] * 100)
                    avg_success_amount = data['success_amount'] / data['successful_orders'] if data[
                                                                                                   'successful_orders'] > 0 else 0

                    log_message += (
                        f"Salesperson {user_id}:\n"
                        f"  - Total Orders: {data['total_orders']}\n"
                        f"  - Successful Orders: {data['successful_orders']}\n"
                        f"  - Average Success Amount: {avg_success_amount:.2f}\n"
                        f"  - Success Rate: {success_rate:.2f}%\n"
                    )

                    chart_data.append({
                        'avg_success_amount': avg_success_amount,
                        'success_rate': success_rate,
                        'total_orders': data['total_orders']
                    })

            # Очищаємо попередній графік
            plt.clf()

            # Створюємо графік
            plt.figure(figsize=(15, 8))

            # Малюємо точки
            plt.scatter([d['avg_success_amount'] for d in chart_data],
                        [d['success_rate'] for d in chart_data],
                        s=100, alpha=0.5)

            # Додаємо мітки з кількістю замовлень біля кожної точки
            for d in chart_data:
                plt.annotate(str(d['total_orders']),
                             (d['avg_success_amount'], d['success_rate']),
                             xytext=(5, 5), textcoords='offset points')

            plt.xlabel('Average Amount of Successful Orders Only')
            plt.ylabel('Success Rate (%)')
            plt.title('Success Rate by Average Amount of Successful Salesperson Orders')

            # Форматуємо вісь X для відображення сум у тисячах
            ax = plt.gca()
            ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x / 1000), ',')))
            plt.xlabel('Average Amount of Successful Orders Only (Thousands)')

            # Додаємо сітку
            plt.grid(True, linestyle='--', alpha=0.7)

            # Зберігаємо графік
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            plt.close()

            # Конвертуємо в base64
            self.salesperson_avg_success_amount_success_chart = base64.b64encode(buffer.getvalue())

        except Exception as e:
            print(f"Error computing salesperson average success amount success chart: {str(e)}")

    def _compute_salesperson_order_intensity_chart(self):
        """Compute chart showing success rate by order intensity for each salesperson"""
        for record in self:
            try:
                # Читаємо дані з CSV
                data = record._read_csv_data()
                if not data:
                    record.salesperson_order_intensity_success_chart = False
                    continue

                # Рахуємо метрики для кожного менеджера
                salesperson_stats = defaultdict(lambda: {
                    'first_order': None,
                    'last_order': None,
                    'total': 0,
                    'success': 0
                })

                # Збираємо статистику по кожному менеджеру
                for row in data:
                    user_id = row['user_id']
                    if not user_id:
                        continue

                    order_date = row['date_order']

                    stats = salesperson_stats[user_id]
                    if not stats['first_order'] or order_date < stats['first_order']:
                        stats['first_order'] = order_date
                    if not stats['last_order'] or order_date > stats['last_order']:
                        stats['last_order'] = order_date

                    stats['total'] += 1
                    if row['state'] in ['done', 'sale']:
                        stats['success'] += 1

                # Створюємо лог перед побудовою графіка
                log_message = "\nOrder Intensity Chart - Final Data:\n"
                chart_data = []

                # Рахуємо success rate та інтенсивність для кожного менеджера
                for user_id, stats in salesperson_stats.items():
                    if stats['first_order'] and stats['last_order'] and stats['total'] >= 5:
                        # Рахуємо місяці між першим і останнім замовленням
                        months_active = ((stats['last_order'] - stats['first_order']).days / 30.44) + 1

                        # Рахуємо інтенсивність замовлень (замовлень на місяць)
                        intensity = stats['total'] / months_active

                        # Рахуємо success rate
                        success_rate = (stats['success'] / stats['total'] * 100)

                        log_message += (
                            f"Salesperson {user_id}:\n"
                            f"  - First Order: {stats['first_order']}\n"
                            f"  - Last Order: {stats['last_order']}\n"
                            f"  - Months Active: {months_active:.2f}\n"
                            f"  - Total Orders: {stats['total']}\n"
                            f"  - Successful Orders: {stats['success']}\n"
                            f"  - Order Intensity: {intensity:.2f} orders/month\n"
                            f"  - Success Rate: {success_rate:.2f}%\n"
                        )

                        chart_data.append({
                            'intensity': intensity,
                            'success_rate': success_rate,
                            'total_orders': stats['total']
                        })

                if not chart_data:
                    print("No data to plot")
                    record.salesperson_order_intensity_success_chart = False
                    continue

                # Очищаємо попередній графік
                plt.clf()

                # Створюємо графік
                plt.figure(figsize=(15, 8))

                # Малюємо точки
                plt.scatter([d['intensity'] for d in chart_data],
                            [d['success_rate'] for d in chart_data],
                            s=100, alpha=0.5)

                # Додаємо мітки з кількістю замовлень біля кожної точки
                for d in chart_data:
                    plt.annotate(str(d['total_orders']),
                                 (d['intensity'], d['success_rate']),
                                 xytext=(5, 5), textcoords='offset points')

                # Додаємо лінію тренду
                intensities = [d['intensity'] for d in chart_data]
                success_rates = [d['success_rate'] for d in chart_data]
                z = np.polyfit(intensities, success_rates, 1)
                p = np.poly1d(z)
                plt.plot(intensities, p(intensities), "r--", alpha=0.8)

                plt.xlabel('Order Intensity (orders per month)')
                plt.ylabel('Success Rate (%)')
                plt.title('Success Rate by Order Intensity per Salesperson\n(number shows total orders)')

                # Додаємо сітку
                plt.grid(True, linestyle='--', alpha=0.7)

                # Зберігаємо графік
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
                plt.close()

                # Конвертуємо в base64
                record.salesperson_order_intensity_success_chart = base64.b64encode(buffer.getvalue())

            except Exception as e:
                print(f"Error computing salesperson order intensity chart: {str(e)}")
                record.salesperson_order_intensity_success_chart = False
                plt.close('all')

    def _compute_salesperson_success_order_intensity_chart(self):
        """Compute chart showing success rate by successful order intensity for each salesperson"""
        for record in self:
            try:
                # Читаємо дані з CSV
                data = record._read_csv_data()
                if not data:
                    record.salesperson_success_order_intensity_chart = False
                    continue

                # Рахуємо метрики для кожного менеджера
                salesperson_stats = defaultdict(lambda: {
                    'first_order': None,
                    'last_order': None,
                    'total': 0,
                    'success': 0
                })

                # Збираємо статистику по кожному менеджеру
                for row in data:
                    user_id = row['user_id']
                    if not user_id:
                        continue

                    order_date = row['date_order']

                    stats = salesperson_stats[user_id]
                    if not stats['first_order'] or order_date < stats['first_order']:
                        stats['first_order'] = order_date
                    if not stats['last_order'] or order_date > stats['last_order']:
                        stats['last_order'] = order_date

                    stats['total'] += 1
                    if row['state'] in ['done', 'sale']:
                        stats['success'] += 1

                # Створюємо лог перед побудовою графіка
                log_message = "\nSuccess Order Intensity Chart - Final Data:\n"
                chart_data = []

                # Рахуємо success rate та інтенсивність для кожного менеджера
                for user_id, stats in salesperson_stats.items():
                    if stats['first_order'] and stats['last_order'] and stats['success'] >= 5:
                        # Рахуємо місяці між першим і останнім замовленням
                        months_active = ((stats['last_order'] - stats['first_order']).days / 30.44) + 1

                        # Рахуємо інтенсивність успішних замовлень (успішних замовлень на місяць)
                        success_intensity = stats['success'] / months_active

                        # Рахуємо success rate
                        success_rate = (stats['success'] / stats['total'] * 100)

                        log_message += (
                            f"Salesperson {user_id}:\n"
                            f"  - First Order: {stats['first_order']}\n"
                            f"  - Last Order: {stats['last_order']}\n"
                            f"  - Months Active: {months_active:.2f}\n"
                            f"  - Total Orders: {stats['total']}\n"
                            f"  - Successful Orders: {stats['success']}\n"
                            f"  - Success Order Intensity: {success_intensity:.2f} orders/month\n"
                            f"  - Success Rate: {success_rate:.2f}%\n"
                        )

                        chart_data.append({
                            'intensity': success_intensity,
                            'success_rate': success_rate,
                            'total_orders': stats['total']
                        })

                if not chart_data:
                    print("No data to plot")
                    record.salesperson_success_order_intensity_chart = False
                    continue

                # Очищаємо попередній графік
                plt.clf()

                # Створюємо графік
                plt.figure(figsize=(15, 8))

                # Малюємо точки
                plt.scatter([d['intensity'] for d in chart_data],
                            [d['success_rate'] for d in chart_data],
                            s=100, alpha=0.5)

                # Додаємо мітки з кількістю замовлень біля кожної точки
                for d in chart_data:
                    plt.annotate(str(d['total_orders']),
                                 (d['intensity'], d['success_rate']),
                                 xytext=(5, 5), textcoords='offset points')

                # Додаємо лінію тренду
                intensities = [d['intensity'] for d in chart_data]
                success_rates = [d['success_rate'] for d in chart_data]
                z = np.polyfit(intensities, success_rates, 1)
                p = np.poly1d(z)
                plt.plot(intensities, p(intensities), "r--", alpha=0.8)

                plt.xlabel('Success Order Intensity (successful orders per month)')
                plt.ylabel('Success Rate (%)')
                plt.title('Success Rate by Successful Order Intensity per Salesperson\n(number shows total orders)')

                # Додаємо сітку
                plt.grid(True, linestyle='--', alpha=0.7)

                # Зберігаємо графік
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
                plt.close()

                # Конвертуємо в base64
                record.salesperson_success_order_intensity_chart = base64.b64encode(buffer.getvalue())

            except Exception as e:
                print(f"Error computing salesperson success order intensity chart: {str(e)}")
                record.salesperson_success_order_intensity_chart = False
                plt.close('all')

    def _compute_salesperson_amount_intensity_chart(self):
        """Compute chart showing success rate by amount intensity for each salesperson"""
        for record in self:
            try:
                # Читаємо дані з CSV
                data = record._read_csv_data()
                if not data:
                    record.salesperson_amount_intensity_success_chart = False
                    continue

                # Рахуємо метрики для кожного менеджера
                salesperson_stats = defaultdict(lambda: {
                    'first_order': None,
                    'last_order': None,
                    'total': 0,
                    'success': 0,
                    'total_amount': 0
                })

                # Збираємо статистику по кожному менеджеру
                for row in data:
                    user_id = row['user_id']
                    if not user_id:
                        continue

                    order_date = row['date_order']
                    amount = float(row['amount_total'])

                    stats = salesperson_stats[user_id]
                    if not stats['first_order'] or order_date < stats['first_order']:
                        stats['first_order'] = order_date
                    if not stats['last_order'] or order_date > stats['last_order']:
                        stats['last_order'] = order_date

                    stats['total'] += 1
                    stats['total_amount'] += amount
                    if row['state'] in ['done', 'sale']:
                        stats['success'] += 1

                # Створюємо лог перед побудовою графіка
                log_message = "\nAmount Intensity Chart - Final Data:\n"
                chart_data = []

                # Рахуємо success rate та інтенсивність для кожного менеджера
                for user_id, stats in salesperson_stats.items():
                    if stats['first_order'] and stats['last_order'] and stats['total'] >= 5:
                        # Рахуємо місяці між першим і останнім замовленням
                        months_active = ((stats['last_order'] - stats['first_order']).days / 30.44) + 1

                        # Рахуємо інтенсивність за сумою (сума на місяць)
                        amount_intensity = stats['total_amount'] / months_active

                        # Рахуємо success rate
                        success_rate = (stats['success'] / stats['total'] * 100)

                        log_message += (
                            f"Salesperson {user_id}:\n"
                            f"  - First Order: {stats['first_order']}\n"
                            f"  - Last Order: {stats['last_order']}\n"
                            f"  - Months Active: {months_active:.2f}\n"
                            f"  - Total Orders: {stats['total']}\n"
                            f"  - Total Amount: {stats['total_amount']:.2f}\n"
                            f"  - Amount Intensity: {amount_intensity:.2f} per month\n"
                            f"  - Success Rate: {success_rate:.2f}%\n"
                        )

                        chart_data.append({
                            'intensity': amount_intensity,
                            'success_rate': success_rate,
                            'total_orders': stats['total']
                        })

                if not chart_data:
                    print("No data to plot")
                    record.salesperson_amount_intensity_success_chart = False
                    continue

                # Очищаємо попередній графік
                plt.clf()

                # Створюємо графік
                plt.figure(figsize=(15, 8))

                # Малюємо точки
                plt.scatter([d['intensity'] for d in chart_data],
                            [d['success_rate'] for d in chart_data],
                            s=100, alpha=0.5)

                # Додаємо мітки з кількістю замовлень біля кожної точки
                for d in chart_data:
                    plt.annotate(str(d['total_orders']),
                                 (d['intensity'], d['success_rate']),
                                 xytext=(5, 5), textcoords='offset points')

                # Додаємо лінію тренду
                intensities = [d['intensity'] for d in chart_data]
                success_rates = [d['success_rate'] for d in chart_data]
                z = np.polyfit(intensities, success_rates, 1)
                p = np.poly1d(z)
                plt.plot(intensities, p(intensities), "r--", alpha=0.8)

                plt.xlabel('Amount Intensity (amount per month)')
                plt.ylabel('Success Rate (%)')
                plt.title('Success Rate by Amount Intensity per Salesperson\n(number shows total orders)')

                # Форматуємо вісь X для відображення сум у тисячах
                ax = plt.gca()
                ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x / 1000), ',')))
                plt.xlabel('Amount Intensity (thousands per month)')

                # Додаємо сітку
                plt.grid(True, linestyle='--', alpha=0.7)

                # Зберігаємо графік
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
                plt.close()

                # Конвертуємо в base64
                record.salesperson_amount_intensity_success_chart = base64.b64encode(buffer.getvalue())

            except Exception as e:
                print(f"Error computing salesperson amount intensity chart: {str(e)}")
                record.salesperson_amount_intensity_success_chart = False
                plt.close('all')

    def _compute_salesperson_success_amount_intensity_chart(self):
        """Compute chart showing success rate by successful amount intensity for each salesperson"""
        for record in self:
            try:
                # Читаємо дані з CSV
                data = record._read_csv_data()
                if not data:
                    record.salesperson_success_amount_intensity_chart = False
                    continue

                # Рахуємо метрики для кожного менеджера
                salesperson_stats = defaultdict(lambda: {
                    'first_order': None,
                    'last_order': None,
                    'total': 0,
                    'success': 0,
                    'success_amount': 0
                })

                # Збираємо статистику по кожному менеджеру
                for row in data:
                    user_id = row['user_id']
                    if not user_id:
                        continue

                    order_date = row['date_order']
                    amount = float(row['amount_total'])

                    stats = salesperson_stats[user_id]
                    if not stats['first_order'] or order_date < stats['first_order']:
                        stats['first_order'] = order_date
                    if not stats['last_order'] or order_date > stats['last_order']:
                        stats['last_order'] = order_date

                    stats['total'] += 1
                    if row['state'] in ['done', 'sale']:
                        stats['success'] += 1
                        stats['success_amount'] += amount

                # Створюємо лог перед побудовою графіка
                log_message = "\nSuccess Amount Intensity Chart - Final Data:\n"
                chart_data = []

                # Рахуємо success rate та інтенсивність для кожного менеджера
                for user_id, stats in salesperson_stats.items():
                    if stats['first_order'] and stats['last_order'] and stats['success'] >= 5:
                        # Рахуємо місяці між першим і останнім замовленням
                        months_active = ((stats['last_order'] - stats['first_order']).days / 30.44) + 1

                        # Рахуємо інтенсивність успішних замовлень за сумою (успішна сума на місяць)
                        success_amount_intensity = stats['success_amount'] / months_active

                        # Рахуємо success rate
                        success_rate = (stats['success'] / stats['total'] * 100)

                        log_message += (
                            f"Salesperson {user_id}:\n"
                            f"  - First Order: {stats['first_order']}\n"
                            f"  - Last Order: {stats['last_order']}\n"
                            f"  - Months Active: {months_active:.2f}\n"
                            f"  - Total Orders: {stats['total']}\n"
                            f"  - Success Amount: {stats['success_amount']:.2f}\n"
                            f"  - Success Amount Intensity: {success_amount_intensity:.2f} per month\n"
                            f"  - Success Rate: {success_rate:.2f}%\n"
                        )

                        chart_data.append({
                            'intensity': success_amount_intensity,
                            'success_rate': success_rate,
                            'total_orders': stats['total']
                        })

                if not chart_data:
                    print("No data to plot")
                    record.salesperson_success_amount_intensity_chart = False
                    continue

                # Очищаємо попередній графік
                plt.clf()

                # Створюємо графік
                plt.figure(figsize=(15, 8))

                # Малюємо точки
                plt.scatter([d['intensity'] for d in chart_data],
                            [d['success_rate'] for d in chart_data],
                            s=100, alpha=0.5)

                # Додаємо мітки з кількістю замовлень біля кожної точки
                for d in chart_data:
                    plt.annotate(str(d['total_orders']),
                                 (d['intensity'], d['success_rate']),
                                 xytext=(5, 5), textcoords='offset points')

                # Додаємо лінію тренду
                intensities = [d['intensity'] for d in chart_data]
                success_rates = [d['success_rate'] for d in chart_data]
                z = np.polyfit(intensities, success_rates, 1)
                p = np.poly1d(z)
                plt.plot(intensities, p(intensities), "r--", alpha=0.8)

                plt.xlabel('Success Amount Intensity (successful amount per month)')
                plt.ylabel('Success Rate (%)')
                plt.title('Success Rate by Successful Amount Intensity per Salesperson\n(number shows total orders)')

                # Форматуємо вісь X для відображення сум у тисячах
                ax = plt.gca()
                ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x / 1000), ',')))
                plt.xlabel('Success Amount Intensity (thousands per month)')

                # Додаємо сітку
                plt.grid(True, linestyle='--', alpha=0.7)

                # Зберігаємо графік
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
                plt.close()

                # Конвертуємо в base64
                record.salesperson_success_amount_intensity_chart = base64.b64encode(buffer.getvalue())

            except Exception as e:
                print(f"Error computing salesperson success amount intensity chart: {str(e)}")
                record.salesperson_success_amount_intensity_chart = False
                plt.close('all')

    def action_compute_salesperson_charts(self):
        """Compute all salesperson analysis charts"""
        self.ensure_one()
        if not self.data_file:
            raise UserError(_('Please collect data or upload a CSV file first.'))

        # Обчислюємо всі графіки для аналізу менеджерів
        self._compute_salesperson_age_success_chart()
        self._compute_salesperson_orders_success_chart()
        self._compute_salesperson_total_amount_success_chart()
        self._compute_salesperson_success_amount_success_chart()
        self._compute_salesperson_avg_amount_success_chart()
        self._compute_salesperson_avg_success_amount_success_chart()
        self._compute_salesperson_order_intensity_chart()
        self._compute_salesperson_success_order_intensity_chart()
        self._compute_salesperson_amount_intensity_chart()
        self._compute_salesperson_success_amount_intensity_chart()
