import csv
import base64
import logging
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
matplotlib.use('Agg')
import numpy as np
import pandas as pd
import seaborn as sns
from io import StringIO, BytesIO
from datetime import datetime
from collections import defaultdict
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)



class DataCollector(models.Model):
    _name = 'data.collector'
    _description = 'Data Collector'

    name = fields.Char(required=True)
    date_from = fields.Date(readonly=True)
    date_to = fields.Date(readonly=True)
    date_range_display = fields.Char(string='Analysis Period', compute='_compute_date_range_display', store=True)

    # Data file fields
    data_file = fields.Binary(string='Data File (CSV)', attachment=True)
    data_filename = fields.Char(string='Data Filename')

    extended_data_file = fields.Binary(string='Extended Data File (CSV)', attachment=True)
    extended_data_filename = fields.Char(string='Extended Data Filename')

    # Statistics fields (computed from CSV data)
    total_partners = fields.Integer(string='Total number of clients', compute='_compute_statistics', store=True)
    total_orders = fields.Integer(string='Total number of orders', compute='_compute_statistics', store=True)
    total_success_rate = fields.Float(string='Total % of successful orders', compute='_compute_statistics', store=True)
    orders_by_state = fields.Text(string='Distribution of orders by status', compute='_compute_statistics', store=True)
    partners_by_success_rate = fields.Text(string='Distribution of customers by success_rate',
                                           compute='_compute_statistics', store=True)

    # Поля для зберігання графіків

    discount_analysis_graph = fields.Binary('Графік аналізу знижок', attachment=True)
    discount_analysis_graph_filename = fields.Char('Filename discount')

    # Time Analysis Graphs
    time_distribution_graph = fields.Binary('Розподіл замовлень за часом', attachment=True)
    time_distribution_filename = fields.Char('Filename time distribution')

    weekly_heatmap_graph = fields.Binary('Тепловий графік по днях тижня', attachment=True)
    weekly_heatmap_filename = fields.Char('Filename weekly heatmap')

    weekly_success_heatmap_graph = fields.Binary('Теплова карта успішності замовлень по днях тижня', attachment=True)
    weekly_success_heatmap_filename = fields.Char('Filename weekly success heatmap')

    seasonal_monthly_graph = fields.Binary('Розподіл та успішність замовлень по місяцях', attachment=True)
    seasonal_monthly_filename = fields.Char('Filename seasonal monthly')

    seasonal_weekday_graph = fields.Binary('Розподіл замовлень по днях тижня', attachment=True)
    seasonal_weekday_filename = fields.Char('Filename seasonal weekday')

    processing_duration_graph = fields.Binary('Графік тривалості обробки', attachment=True)
    processing_duration_filename = fields.Char('Filename processing')

    # Customer Analysis Graphs
    customer_history_graph = fields.Binary('Аналіз історії клієнтів', attachment=True)
    customer_history_filename = fields.Char('Filename customer history')

    customer_relationship_graph = fields.Binary('Аналіз терміну співпраці', attachment=True)
    customer_relationship_filename = fields.Char('Filename relationship')

    customer_relationship_distribution_graph = fields.Binary('Розподіл замовлень за тривалістю співпраці',
                                                             attachment=True)
    customer_relationship_distribution_filename = fields.Char('Filename customer relationship distribution')

    # Order Parameters Graphs
    amount_correlation_graph = fields.Binary('Кореляція суми замовлення', attachment=True)
    amount_correlation_filename = fields.Char('Filename amount correlation')

    product_lines_graph = fields.Binary('Аналіз кількості позицій', attachment=True)
    product_lines_filename = fields.Char('Filename product lines')

    payment_analysis_graph = fields.Binary('Аналіз способів оплати', attachment=True)
    payment_analysis_filename = fields.Char('Filename payment')

    delivery_analysis_graph = fields.Binary('Аналіз умов доставки', attachment=True)
    delivery_analysis_filename = fields.Char('Filename delivery')

    changes_messages_correlation_graph = fields.Binary('Залежність змін від повідомлень', attachment=True)
    changes_messages_correlation_filename = fields.Char('Filename changes messages correlation')

    # Interaction Analysis Graphs
    changes_impact_graph = fields.Binary('Вплив змін на успішність', attachment=True)
    changes_impact_filename = fields.Char('Filename changes')

    customer_avg_changes_graph = fields.Binary('Аналіз клієнтів за середньою кількістю змін', attachment=True)
    customer_avg_changes_filename = fields.Char('Filename customer avg changes')

    communication_analysis_graph = fields.Binary('Аналіз комунікацій', attachment=True)
    communication_analysis_filename = fields.Char('Filename communication')

    customer_avg_messages_graph = fields.Binary('Аналіз клієнтів за середньою кількістю повідомлень', attachment=True)
    customer_avg_messages_filename = fields.Char('Filename customer avg messages')

    customer_amount_success_distribution_graph = fields.Binary('Розподіл успішності за сумою замовлення',
                                                               attachment=True)
    customer_amount_success_distribution_filename = fields.Char('Filename customer amount success distribution')
    customer_amount_success_distribution_plot = fields.Binary('Розподіл успішності за сумою замовлення',
                                                               attachment=True)

    # Sales Performance Graphs
    manager_performance_graph = fields.Binary('Ефективність менеджерів', attachment=True)
    manager_performance_filename = fields.Char('Filename manager')

    # Поля для розширеної статистики
    total_sale_orders = fields.Integer('Всього замовлень', readonly=True)
    success_rate = fields.Float('Відсоток успішних замовлень', readonly=True)
    avg_response_time = fields.Float('Середній час відповіді (години)', readonly=True)
    avg_processing_time = fields.Float('Середній час обробки (години)', readonly=True)

    orders_by_state_chart = fields.Binary(string='Orders by Status Distribution',
                                          compute='_compute_distribution_charts', store=True)
    partners_by_rate_chart = fields.Binary(string='Partners by Success Rate Distribution',
                                           compute='_compute_distribution_charts', store=True)
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
    avg_amount_success_chart = fields.Binary(
        string='Success Rate by Average Order Amount',
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
            self.data_filename = f'sales_data_{fields.Date.today()}.csv'

            return True

        except Exception as e:
            raise UserError(_('Error collecting data: %s') % str(e))

    def action_collect_extended_data(self):
        """Collect extended data from database and save to CSV"""
        self.ensure_one()
        self.extended_data_file = False
        self.extended_data_filename = False

        try:
            # Get sale orders
            orders = self.env['sale.order'].search([])
            print(f"\nFound {len(orders)} orders")

            # Prepare CSV data
            csv_data = self._prepare_csv_extended_data(orders)
            print(f"Prepared {len(csv_data)} rows of data")

            # Convert to CSV
            output = StringIO()
            writer = csv.writer(output)
            writer.writerows(csv_data)

            # Save to binary field
            self.extended_data_file = base64.b64encode(output.getvalue().encode('utf-8'))
            self.extended_data_filename = f'extended_data_{fields.Date.today()}.csv'

            return True

        except Exception as e:
            raise UserError(_('Error collecting data: %s') % str(e))

    def _prepare_csv_extended_data(self, sale_orders):
        """Prepare raw extended data for CSV file"""
        print("\nPreparing CSV extended data...")

        # Визначаємо заголовки для CSV
        headers = [
            'order_id',
            'create_date',
            'date_order',
            'processing_time_hours',
            'day_of_week',
            'month',
            'quarter',
            'hour_of_day',
            'customer_id',
            'customer_category',
            'customer_country',
            'customer_relationship_days',
            'previous_orders_count',
            'total_amount',
            'order_lines_count',
            'product_categories',
            'discount_total',
            'payment_term',
            'delivery_method',
            'changes_count',
            'messages_count',
            'salesperson',
            'sales_team',
            'source',
            'state',
        ]

        rows = []  # Тут будуть зберігатися рядки даних

        # Обробляємо кожне замовлення
        for order in sale_orders:
            # Розрахунок часових параметрів
            create_date = fields.Datetime.from_string(order.create_date)
            date_order = fields.Datetime.from_string(order.date_order) if order.date_order else create_date

            processing_time = None
            if date_order and create_date:
                processing_time = (date_order - create_date).total_seconds() / 3600

            # Підрахунок попередніх замовлень
            previous_orders = self.env['sale.order'].search_count([
                ('partner_id', '=', order.partner_id.id),
                ('create_date', '<', order.create_date),
                ('state', 'in', ['sale', 'done'])
            ])

            # Підрахунок змін у замовленні
            changes_count = self.env['mail.message'].search_count([
                ('model', '=', 'sale.order'),
                ('res_id', '=', order.id),
                ('tracking_value_ids', '!=', False)
            ])

            # Формуємо рядок даних
            row = [
                order.name,  # order_id
                create_date,  # create_date
                date_order,  # confirmation_date
                processing_time,  # processing_time_hours
                create_date.strftime('%A'),  # day_of_week
                create_date.strftime('%B'),  # month
                (create_date.month - 1) // 3 + 1,  # quarter
                create_date.hour,  # hour_of_day
                order.partner_id.id,  # customer_id
                ', '.join(order.partner_id.category_id.mapped('name')),  # customer_category
                order.partner_id.country_id.name,  # customer_country
                (create_date.date() - order.partner_id.create_date.date()).days,  # customer_relationship_days
                previous_orders,  # previous_orders_count
                order.amount_total,  # total_amount
                len(order.order_line),  # order_lines_count
                ', '.join(set(order.order_line.mapped('product_id.categ_id.name'))),  # product_categories
                sum(line.discount for line in order.order_line),  # discount_total
                order.payment_term_id.name,  # payment_term
                order.carrier_id.name,  # delivery_method
                changes_count,  # changes_count
                len(order.message_ids),  # messages_count
                f'user-1-{order.user_id.id}',  # salesperson
                f'team-1-{order.team_id.id}',  # sales_team
                order.source_id.name if hasattr(order, 'source_id') else None,  # source
                order.state
            ]

            if len(rows) == 3:
                print(f"ROWS: {rows}")

            rows.append(row)
        print(f"CSV extended data prepared. Total rows: {len(rows)}")
        csv_data = [headers] + rows
        return csv_data

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
            if len(csv_data) == 2:
                print(f"CSV_DATA: {csv_data}")

        print(f"CSV data prepared. Total rows: {len(csv_data)}")
        return csv_data

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

    def _read_csv_extended_data(self):
        print("Starting _read_csv_extended_data")
        if not self.data_file:
            print("No extended data file found")
            return []
        try:
            # Decode base64 data
            csv_data = base64.b64decode(self.extended_data_file).decode('utf-8')
            print("Successfully decoded CSV extended data")

            # Read CSV data
            csv_file = StringIO(csv_data)
            reader = csv.DictReader(csv_file)
            data = []
            for row in reader:
                try:
                    # Обрізаємо мікросекунди з дат
                    if 'create_date' in row:
                        date_str = row['create_date'].split('.')[0]  # Видаляємо мікросекунди
                        row['create_date'] = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    if 'date_order' in row:
                        date_str = row['date_order'].split('.')[0]  # Видаляємо мікросекунди
                        row['date_order'] = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    continue

                # try:
                #     if 'partner_create_date' in row:
                #         date_str = row['partner_create_date'].split('.')[0]  # Видаляємо мікросекунди
                #         row['partner_create_date'] = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                # except ValueError:
                #     continue

                # Ensure required fields are present
                if not all(field in row for field in
                           [
                               'order_id',
                               'create_date',
                               'date_order',
                               'processing_time_hours',
                               'day_of_week',
                               'month',
                               'quarter',
                               'hour_of_day',
                               'customer_id',
                               'customer_category',
                               'customer_country',
                               'customer_relationship_days',
                               'previous_orders_count',
                               'total_amount',
                               'order_lines_count',
                               'product_categories',
                               'discount_total',
                               'payment_term',
                               'delivery_method',
                               'changes_count',
                               'messages_count',
                               'salesperson',
                               'sales_team',
                               'source',
                               'state',
                           ]):
                    print(f"Missing required fields in row: {row}")
                    continue

                data.append(row)

            print(f"Successfully read {len(data)} rows from CSV")
            return data

        except Exception as e:
            print(f"Error reading CSV data: {str(e)}")
            return []

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

    def _compute_statistics(self):
        print("Starting _compute_statistics")
        for record in self:
            print(f"Processing record {record.id}")

            # Read CSV data
            data = record._read_csv_data()
            print(f"Read {len(data)} rows from CSV for record {record.id}")
            if not data:
                continue

            # Read extended CSV data
            extended_data = record._read_csv_extended_data()
            print(f"Read {len(extended_data)} rows from extended CSV for record {record.id}")

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

            extended_partners = set()  # для розширених даних
            # Process extended data
            if extended_data:
                for row in extended_data:
                    customer_id = int(row['customer_id'])
                    extended_partners.add(customer_id)

            # Print comparison
            print(f"\nPartners count comparison for record {record.id}:")
            print(f"Basic data partners: {len(partners)}")
            print(f"Extended data partners: {len(extended_partners)}")
            if len(partners) != len(extended_partners):
                print("WARNING: Number of partners differs between basic and extended data!")
                print("Partners only in basic data:", len(partners - extended_partners))
                print("Partners only in extended data:", len(extended_partners - partners))

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

            print(f"Updated statistics for record {record.id}")

    def action_compute_statistics(self):
        if not self.data_file:
            raise UserError(_('Please collect data or upload a CSV file first.'))
        self._compute_statistics()

    def save_plot_to_binary(self, plt_figure, filename):
        """Зберігає графік matplotlib у бінарне поле"""
        buffer = BytesIO()
        plt_figure.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()), filename

    def analyze_discounts(self, df):
        """Аналіз впливу знижок на успішність замовлень"""
        fig, ax1 = plt.subplots(figsize=(10, 6))

        try:
            # Підготовка даних
            df['has_discount'] = df['discount_total'] > 0
            df['is_successful'] = df['state'] == 'sale'

            # Аналіз успішності
            success_by_discount = df.groupby('has_discount')['is_successful'].agg(['mean', 'count'])
            total_orders = len(df)

            # Створення основного графіка
            x = np.arange(len(success_by_discount))
            bars = ax1.bar(x, success_by_discount['mean'].values * 100, color='#1f77b4')

            # Налаштування осей
            ax1.set_ylabel('Відсоток успішності (%)')
            ax1.set_ylim(0, 100)
            ax1.set_xticks(x)
            labels = ['Без знижки', 'Зі знижкою']
            ax1.set_xticklabels(labels)

            # Додаємо підписи значень
            for i, v in enumerate(success_by_discount['mean'].values):
                count = success_by_discount['count'].values[i]
                percentage = count / total_orders * 100
                ax1.text(i, v * 100 + 1,
                         f'{v:.1%}\n{count:,} замовлень\n({percentage:.1f}% від всіх)',
                         ha='center', va='bottom')

            # Додаємо середню лінію успішності
            avg_success = df['is_successful'].mean() * 100
            ax1.axhline(y=avg_success, color='skyblue', linestyle='--', alpha=0.5)
            ax1.text(-0.2, avg_success - 5, f'Середня успішність: {avg_success:.1f}%',
                     color='skyblue', alpha=0.7)

            plt.title('Аналіз впливу знижок на успішність замовлень')

            # Додаємо статистичну інформацію
            orders_with_discount = success_by_discount.loc[True, 'count']
            total_discount_amount = df[df['has_discount']]['discount_total'].sum()
            avg_discount = df[df['has_discount']]['discount_total'].mean()

            info_text = (
                f"Статистика знижок:\n"
                f"Всього замовлень зі знижкою: {orders_with_discount:,}\n"
                f"Загальна сума знижок: {total_discount_amount:,.2f}\n"
                f"Середня знижка: {avg_discount:.2f}"
            )
            plt.figtext(1.02, 0.5, info_text, fontsize=8, va='center')

            # Збільшуємо відступи для тексту справа
            plt.subplots_adjust(right=0.85)

            return self.save_plot_to_binary(fig, 'discount_analysis.png')
        except Exception as e:
            _logger.error(f"Помилка при аналізі знижок: {e}")
            return None
        finally:
            plt.close()

    def analyze_time_distribution(self, df):
        """Аналіз розподілу замовлень за часом доби"""
        plt.figure(figsize=(15, 6))
        print(f"DF columns: {df.columns}")
        print(f"Unique states in DF: {df['state'].unique()}")
        print(f"hour_of_day dtype: {df['hour_of_day'].dtype}")
        print(f"Sample of hour_of_day values: {df['hour_of_day'].head()}")

        # Створюємо повний діапазон годин та ініціалізуємо їх нулями
        hours_range = range(24)
        print(f"hours_range: {hours_range}")
        hour_counts = pd.Series(0, index=hours_range, name='orders')
        success_rates = pd.Series(0.0, index=hours_range, name='success_rate')
        print(f"hour_counts: {hour_counts}")

        # Підраховуємо кількість замовлень для кожної години
        temp_counts = df['hour_of_day'].value_counts()
        print(f"temp_counts: {temp_counts}")

        # Розраховуємо відсоток успішних замовлень для кожної години
        print("\nРозрахунок відсотка успішних замовлень по годинах:")
        for hour in hours_range:
            # Конвертуємо hour_of_day в int для коректного порівняння
            df['hour_int'] = df['hour_of_day'].astype(int)

            # Фільтруємо замовлення для поточної години
            hour_orders = df[df['hour_int'] == hour]
            total_orders = len(hour_orders)

            print(f"\nГодина {hour:02d}:")
            print(f"Всього замовлень: {total_orders}")
            if total_orders > 0:
                success_orders = len(hour_orders[hour_orders['state'] == 'sale'])
                print(f"Успішних замовлень: {success_orders}")
                success_rate = (success_orders / total_orders) * 100
                print(f"Відсоток успішних: {success_rate:.1f}%")
                success_rates[hour] = success_rate

                # Додаткове логування для перевірки
                print(f"Розподіл станів для години {hour}:")
                print(hour_orders['state'].value_counts())

        # Конвертуємо індекси в int та оновлюємо значення
        for hour, count in temp_counts.items():
            hour_int = int(hour)  # Явно конвертуємо в int
            if 0 <= hour_int < 24:  # Перевіряємо, що година в правильному діапазоні
                hour_counts[hour_int] = count

        print(f"\nhour_counts after update: {hour_counts}")
        print(f"success_rates: {success_rates}")

        # Створення графіку
        fig, ax1 = plt.subplots(figsize=(15, 6))

        # Налаштування основного графіка (кількість замовлень)
        ax1.bar(range(24), hour_counts, color='skyblue')
        ax1.set_title('Розподіл замовлень за годинами доби')
        ax1.set_xlabel('Година')
        ax1.set_ylabel('Кількість замовлень')
        ax1.grid(True, linestyle='--', alpha=0.7, axis='y')

        # Налаштування другої осі Y для відсотків
        ax2 = ax1.twinx()
        ax2.plot(range(24), success_rates, 'o-', color='gold', linewidth=2, markersize=8)
        ax2.set_ylabel('Відсоток успішних замовлень (%)')

        # Встановлюємо діапазон для відсотків від 0 до 100
        ax2.set_ylim([0, 100])

        # Налаштовуємо відображення годин на осі X
        ax1.set_xticks(range(24))
        ax1.set_xticklabels([f"{i:02d}" for i in range(24)])

        # Додавання підписів значень для кількості замовлень
        for i, v in enumerate(hour_counts):
            if v > 0:  # Показуємо підписи тільки для ненульових значень
                ax1.text(i, v, str(int(v)), ha='center', va='bottom')

        # Додавання підписів значень для відсотків
        for i, v in enumerate(success_rates):
            if hour_counts[i] > 0:  # Показуємо відсотки тільки там, де є замовлення
                ax2.text(i, v, f"{v:.1f}%", ha='center', va='bottom')

        plt.tight_layout()
        return self.save_plot_to_binary(plt.gcf(), 'time_distribution.png')

    def analyze_weekly_heatmap(self, df):
        """Створення теплової карти активності по днях тижня"""
        plt.figure(figsize=(16, 8))

        # Конвертуємо hour_of_day в int та сортуємо
        df['hour_of_day'] = pd.to_numeric(df['hour_of_day'], errors='coerce')

        # Створення зведеної таблиці з впорядкованими годинами
        pivot_table = pd.crosstab(
            index=df['day_of_week'],
            columns=df['hour_of_day'],
            margins=False
        )

        # Забезпечуємо наявність всіх годин від 0 до 23
        for hour in range(24):
            if hour not in pivot_table.columns:
                pivot_table[hour] = 0

        # Сортуємо колонки
        pivot_table = pivot_table.reindex(columns=range(24))

        # Сортуємо дні тижня
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        pivot_table = pivot_table.reindex(days_order)

        # Створення теплової карти
        sns.heatmap(pivot_table,
                    cmap='YlOrRd',
                    annot=True,
                    fmt='d',
                    cbar_kws={'label': 'Кількість замовлень'})

        plt.title('Теплова карта активності замовлень')
        plt.xlabel('Година доби')
        plt.ylabel('День тижня')

        return self.save_plot_to_binary(plt.gcf(), 'weekly_heatmap.png')

    def analyze_weekly_success_heatmap(self, df):
        """Створення теплової карти успішності замовлень по днях тижня"""
        print("\nПочинаємо аналіз успішності замовлень по днях тижня")
        print(f"Всього рядків у DataFrame: {len(df)}")
        print(f"Унікальні дні тижня: {df['day_of_week'].unique()}")
        print(f"Приклад значень day_of_week: {df['day_of_week'].head()}")
        print(f"Тип даних day_of_week: {df['day_of_week'].dtype}")

        print(f"\nУнікальні години: {df['hour_of_day'].unique()}")
        print(f"Приклад значень hour_of_day: {df['hour_of_day'].head()}")
        print(f"Тип даних hour_of_day: {df['hour_of_day'].dtype}")

        print(f"\nУнікальні стани замовлень: {df['state'].unique()}")
        print(f"Розподіл станів:")
        print(df['state'].value_counts())

        plt.figure(figsize=(16, 8))

        # Конвертуємо hour_of_day в int
        df['hour_of_day'] = pd.to_numeric(df['hour_of_day'], errors='coerce')

        # Визначаємо правильний порядок днів тижня
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        # Створюємо DataFrame для відсотка успішних замовлень з типом float64
        success_rates = pd.DataFrame(0.0,
                                     index=days_order,  # Використовуємо впорядкований список днів
                                     columns=range(24),
                                     dtype=np.float64)

        print("\nСтворено порожній DataFrame для success_rates:")
        print(success_rates)
        print(f"Типи даних success_rates:")
        print(success_rates.dtypes)

        # Розраховуємо відсоток успішних замовлень для кожної комбінації день-година
        for day in days_order:  # Використовуємо впорядкований список днів
            print(f"\nАналіз для дня: {day}")
            for hour in range(24):
                # Фільтруємо замовлення для поточної комбінації день-година
                mask = (df['day_of_week'] == day) & (df['hour_of_day'] == hour)
                day_hour_orders = df[mask]
                total = len(day_hour_orders)

                print(f"Година {hour:02d}:")
                print(f"Умови фільтрації: day_of_week == '{day}' & hour_of_day == {hour}")
                print(f"Знайдено рядків: {total}")

                if total > 0:
                    success = len(day_hour_orders[day_hour_orders['state'] == 'sale'])
                    success_rate = float((success / total) * 100)
                    print(f"Успішних замовлень: {success}")
                    print(f"Відсоток успішних: {success_rate:.1f}%")
                    success_rates.loc[day, hour] = success_rate

                    # Додаткова інформація про стани
                    print("Розподіл за станами:")
                    print(day_hour_orders['state'].value_counts())
                else:
                    success_rates.loc[day, hour] = 0.0
                    print("Немає замовлень")

        print("\nФінальна матриця success_rates:")
        print(success_rates)
        print(f"\nТипи даних фінальної матриці:")
        print(success_rates.dtypes)
        print(f"\nІнформація про фінальну матрицю:")
        print(success_rates.info())

        # Створюємо теплову карту
        sns.heatmap(success_rates.astype(float),
                    cmap='YlOrRd',
                    annot=True,
                    fmt='.1f',
                    cbar_kws={'label': 'Відсоток успішних замовлень (%)'})

        plt.title('Розподіл успішності замовлень по днях тижня та годинах')
        plt.xlabel('Година')
        plt.ylabel('День тижня')

        return self.save_plot_to_binary(plt.gcf(), 'weekly_success_heatmap.png')

    def analyze_seasonal_monthly(self, df):
        """Аналіз розподілу та успішності замовлень по місяцях"""
        plt.figure(figsize=(12, 8))

        # Конвертуємо дати в datetime
        df['create_date'] = pd.to_datetime(df['create_date'])

        # Визначаємо успішність на основі state == 'sale'
        df['is_successful'] = df['state'] == 'sale'

        # Аналіз по місяцях
        df['month'] = df['create_date'].dt.month
        monthly_counts = df.groupby('month').size()
        monthly_success = df.groupby('month')['is_successful'].mean() * 100  # Конвертуємо в відсотки

        month_names = ['Січень', 'Лютий', 'Березень', 'Квітень', 'Травень', 'Червень',
                       'Липень', 'Серпень', 'Вересень', 'Жовтень', 'Листопад', 'Грудень']

        # Створюємо основний графік для кількості замовлень
        fig, ax1 = plt.subplots(figsize=(16, 8))

        # Налаштовуємо першу вісь (кількість замовлень)
        x = np.arange(len(monthly_counts))
        bars = ax1.bar(x, monthly_counts.values, color='skyblue')
        ax1.set_xlabel('Місяць')
        ax1.set_ylabel('Кількість замовлень', color='black')
        ax1.tick_params(axis='y', labelcolor='black')

        # Додаємо підписи кількості замовлень
        total_orders = len(df)
        for i, v in enumerate(monthly_counts.values):
            percentage = v / total_orders * 100
            ax1.text(i, v, f'{v}\n({percentage:.1f}%)', ha='center', va='bottom')

        # Створюємо другу вісь для відсотків
        ax2 = ax1.twinx()
        success_line = ax2.plot(x, monthly_success.values, 'o-', color='gold', linewidth=2,
                                markersize=8, label='% успішних')
        ax2.set_ylabel('Відсоток успішних замовлень', color='black')
        ax2.tick_params(axis='y', labelcolor='black')

        # Додаємо підписи відсотків успішності
        for i, v in enumerate(monthly_success.values):
            ax2.text(i, v + 2, f'{v:.1f}%', ha='center', va='bottom', color='black')

        # Налаштовуємо діапазон осей для кращої читабельності
        ax1.set_ylim(0, max(monthly_counts.values) * 1.2)  # 20% відступ зверху для підписів
        ax2.set_ylim(0, 100)  # Відсотки від 0 до 100

        # Налаштовуємо підписи місяців
        plt.xticks(x, [month_names[i-1] for i in monthly_counts.index], rotation=45)

        # Додаємо заголовок
        plt.title('Розподіл та успішність замовлень по місяцях')

        # Додаємо легенду
        ax1.legend(bars, ['Кількість замовлень'], loc='upper left')
        ax2.legend(success_line, ['% успішних'], loc='upper right')

        plt.tight_layout()
        return self.save_plot_to_binary(fig, 'seasonal_monthly.png')

    def analyze_seasonal_weekday(self, df):
        """Аналіз розподілу та успішності замовлень по днях тижня"""
        plt.figure(figsize=(12, 8))

        # Визначаємо успішність на основі state == 'sale'
        df['is_successful'] = df['state'] == 'sale'

        # Визначаємо правильний порядок днів тижня
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        days_ukr = ['Понеділок', 'Вівторок', 'Середа', 'Четвер', 'П\'ятниця', 'Субота', 'Неділя']

        # Підрахунок замовлень та успішності по днях
        weekday_counts = df.groupby('day_of_week').size().reindex(days_order)
        weekday_success = df.groupby('day_of_week')['is_successful'].mean().reindex(days_order) * 100

        # Створюємо основний графік
        fig, ax1 = plt.subplots(figsize=(12, 8))

        # Налаштовуємо першу вісь (кількість замовлень)
        x = np.arange(len(days_ukr))
        bars = ax1.bar(x, weekday_counts.values, color='skyblue')
        ax1.set_xlabel('День тижня')
        ax1.set_ylabel('Кількість замовлень')
        ax1.tick_params(axis='y')

        # Додаємо підписи кількості замовлень
        total_orders = len(df)
        for i, v in enumerate(weekday_counts.values):
            percentage = v / total_orders * 100
            ax1.text(i, v, f'{v}\n({percentage:.1f}%)', ha='center', va='bottom')

        # Створюємо другу вісь для відсотків
        ax2 = ax1.twinx()
        success_line = ax2.plot(x, weekday_success.values, 'o-', color='gold', linewidth=2,
                              markersize=8, label='% успішних')
        ax2.set_ylabel('Відсоток успішних замовлень')
        ax2.tick_params(axis='y')

        # Додаємо підписи відсотків успішності
        for i, v in enumerate(weekday_success.values):
            ax2.text(i, v + 2, f'{v:.1f}%', ha='center', va='bottom')

        # Налаштовуємо діапазон осей
        ax1.set_ylim(0, max(weekday_counts.values) * 1.2)
        ax2.set_ylim(0, 100)

        # Налаштовуємо підписи осі X
        plt.xticks(x, days_ukr, rotation=45)

        plt.title('Розподіл та успішність замовлень по днях тижня')
        plt.tight_layout()

        return self.save_plot_to_binary(plt.gcf(), 'seasonal_weekday.png')

    def analyze_processing_duration(self, df):
        """Аналіз впливу тривалості обробки замовлення на успішність"""
        plt.figure(figsize=(15, 8))

        # Add logging for total orders and states
        total_orders = len(df)
        state_counts = df['state'].value_counts()

        print("\n=== Processing Duration Analysis - Order Statistics ===")
        print(f"Total orders: {total_orders}")
        print("\nOrders by state:")
        for state, count in state_counts.items():
            percentage = (count / total_orders) * 100
            print(f"- {state}: {count} ({percentage:.1f}%)")
        print("================================================\n")

        # Підготовка даних про тривалість обробки
        df['processing_time_hours'] = pd.to_numeric(df['processing_time_hours'], errors='coerce')
        df['processing_days'] = df['processing_time_hours'] / 24

        # Створюємо межі для категорій на основі днів
        duration_bins = [0, 1, 2, 5, 10, float('inf')]
        duration_labels = ['До 1 дня', '1-2 дні', '2-5 днів', '5-10 днів', '10+ днів']

        df['duration_category'] = pd.cut(
            df['processing_days'],
            bins=duration_bins,
            labels=duration_labels,
            include_lowest=True
        )

        # Підрахунок замовлень по тривалості обробки та статусам
        duration_counts = df['duration_category'].value_counts().sort_index()
        success_counts = df[df['state'] == 'sale'].groupby('duration_category').size()
        draft_counts = df[df['state'] == 'draft'].groupby('duration_category').size()
        cancel_counts = df[df['state'] == 'cancel'].groupby('duration_category').size()

        # Створюємо основний графік
        fig, ax1 = plt.subplots(figsize=(15, 8))

        # Налаштовуємо першу вісь (кількість замовлень)
        x = np.arange(len(duration_labels))
        bars = ax1.bar(x, duration_counts.values, color='skyblue', label='Кількість замовлень')
        ax1.set_xlabel('Тривалість обробки')
        ax1.set_ylabel('Кількість замовлень')
        ax1.tick_params(axis='y')

        # Додаємо підписи кількості замовлень з деталізацією
        for i, v in enumerate(duration_counts.values):
            percentage = v / total_orders * 100
            success = success_counts.get(duration_labels[i], 0)
            draft = draft_counts.get(duration_labels[i], 0)
            cancel = cancel_counts.get(duration_labels[i], 0)

            success_percentage = success / total_orders * 100

            label = f'{v}\n({percentage:.1f}%)\n'
            label += f'sale: {success}\n'
            label += f'draft: {draft}\n'
            label += f'cancel: {cancel}'

            ax1.text(i, v, label, ha='center', va='bottom')

        # Налаштовуємо діапазон осей
        y_max = max(duration_counts.values) * 1.2  # 20% відступ для підписів
        ax1.set_ylim(0, y_max)

        # Розраховуємо відсоток успішності відносно загальної кількості замовлень
        success_rate = (success_counts / total_orders * 100).fillna(0)

        # Створюємо другу вісь для відсотків
        ax2 = ax1.twinx()
        success_line = ax2.plot(x, success_rate.values, 'o-', color='gold', linewidth=2,
                                markersize=8, label='% від загальної кількості')
        ax2.set_ylabel('Відсоток від загальної кількості замовлень')
        ax2.tick_params(axis='y')
        ax2.set_ylim(0, 100)

        # Додаємо підписи відсотків успішності
        for i, v in enumerate(success_rate.values):
            # Створюємо текст з відсотком у червоному колі
            bbox_props = dict(
                boxstyle='circle',  # круглий стиль
                facecolor='red',  # червоний колір фону
                alpha=0.3,  # прозорість фону
                edgecolor='red',  # червоний колір обводки
                pad=0.5  # відступ тексту від країв кола
            )

            ax2.text(i - 0.1, v - 1, f'{v:.1f}%',
                     ha='right', va='top',
                     rotation=45,
                     color='black',
                     bbox=bbox_props)

        # Налаштовуємо підписи осі X
        plt.xticks(x, duration_labels, rotation=45)

        # Додаємо заголовок
        plt.title('Розподіл тривалості обробки замовлень та їх успішність')

        # Об'єднуємо легенди обох осей
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

        # Додаємо інформацію про межі категорій
        info_text = 'Межі категорій (дні):\n' + '\n'.join([
            f'{duration_labels[i]}: {duration_bins[i]} - {duration_bins[i + 1]}'
            for i in range(len(duration_labels))
        ])
        plt.figtext(1.02, 0.5, info_text, fontsize=8, va='center')

        plt.tight_layout()
        return self.save_plot_to_binary(plt.gcf(), 'processing_duration.png')

    def analyze_customer_history(self, df):
        """Аналіз впливу історії замовлень клієнта"""
        fig, ax1 = plt.subplots(figsize=(12, 6))

        # Конвертуємо previous_orders_count в числовий формат
        df['previous_orders_count'] = pd.to_numeric(df['previous_orders_count'], errors='coerce').fillna(0).astype(int)

        # Використовуємо previous_orders_count для категоризації
        def get_order_category(row):
            count = int(row['previous_orders_count'])
            if count == 0:
                return 'Нові'
            elif 1 <= count <= 4:
                return '2-5 замовлень'
            elif 5 <= count <= 9:
                return '6-10 замовлень'
            elif 10 <= count <= 19:
                return '11-20 замовлень'
            else:
                return '20+ замовлень'

        # Визначаємо порядок категорій
        category_order = ['Нові', '2-5 замовлень', '6-10 замовлень', '11-20 замовлень', '20+ замовлень']

        # Застосування категоризації до всіх замовлень
        df['customer_category'] = df.apply(get_order_category, axis=1)

        # Визначаємо успішність на основі state == 'sale'
        df['is_successful'] = df['state'] == 'sale'

        # Отримуємо останнє замовлення для кожного клієнта
        latest_orders = df.sort_values('date_order').groupby('customer_id').last()

        # Категоризуємо клієнтів на основі їх останнього замовлення
        latest_orders['customer_category'] = latest_orders.apply(get_order_category, axis=1)

        # Рахуємо кількість клієнтів в кожній категорії
        category_counts = latest_orders['customer_category'].value_counts()
        category_counts = category_counts.reindex(category_order)

        # Рахуємо кількість замовлень в кожній категорії
        orders_counts = df['customer_category'].value_counts()
        orders_counts = orders_counts.reindex(category_order)

        # Рахуємо відсоток успішності для кожної категорії (використовуємо всі замовлення)
        success_by_category = df.groupby('customer_category')['is_successful'].mean()
        success_by_category = success_by_category.reindex(category_order)

        # Створюємо позиції для стовпчиків
        x = np.arange(len(category_counts))
        width = 0.35  # ширина стовпчика

        # Створюємо стовпчики для клієнтів (зліва від центру)
        bars1 = ax1.bar(x - width / 2, category_counts.values, width,
                        color='#1f77b4', label='Кількість клієнтів')
        ax1.set_xlabel('Категорія')
        ax1.set_ylabel('Кількість клієнтів', color='#1f77b4')
        ax1.tick_params(axis='y', labelcolor='#1f77b4')

        # Створюємо другу вісь для замовлень
        ax3 = ax1.twinx()
        ax3.spines['right'].set_position(('outward', 60))
        # Створюємо стовпчики для замовлень (справа від центру)
        bars2 = ax3.bar(x + width / 2, orders_counts.values, width,
                        color='skyblue', label='Кількість замовлень')
        ax3.set_ylabel('Кількість замовлень', color='blue')
        ax3.tick_params(axis='y', labelcolor='blue')

        # Створюємо третю вісь для відсотка успішності
        ax2 = ax1.twinx()
        success_line = ax2.plot(x, success_by_category.values * 100, 'o-',
                                color='gold', linewidth=2, markersize=8)
        ax2.set_ylabel('Відсоток успішності (%)', color='black')
        ax2.tick_params(axis='y', labelcolor='black')
        ax2.set_ylim(0, 100)

        # Налаштовуємо мітки осі X
        ax1.set_xticks(x)
        ax1.set_xticklabels(category_order, rotation=45)
        ax1.set_title('Розподіл клієнтів та замовлень за кількістю попередніх замовлень')

        # Додаємо підписи значень для клієнтів
        for i, v in enumerate(category_counts.values):
            ax1.text(x[i] - width / 2, v, f'{int(v):,}',
                     ha='center', va='bottom', color='#1f77b4')

        # Додаємо підписи значень для замовлень
        for i, v in enumerate(orders_counts.values):
            ax3.text(x[i] + width / 2, v, f'{int(v):,}',
                     ha='center', va='bottom', color='blue')

        # Додаємо підписи для відсотка успішності
        for i, v in enumerate(success_by_category.values):
            ax2.text(i, v * 100 + 2, f'{v:.1%}',
                     ha='center', va='bottom', color='black')

        # Додаємо легенду
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2 = [Line2D([0], [0], color='gold', marker='o', linewidth=2, markersize=8)]
        lines3, labels3 = ax3.get_legend_handles_labels()

        ax1.legend(lines1 + lines3 + lines2,
                   ['Кількість клієнтів', 'Кількість замовлень', 'Відсоток успішності'],
                   loc='upper right')

        # Налаштування відступів
        plt.tight_layout()

        return self.save_plot_to_binary(fig, 'customer_history.png')

    def analyze_geographic_distribution(self, df):
        """Аналіз географічного розподілу замовлень"""
        plt.figure(figsize=(15, 6))

        # Підрахунок замовлень по країнах
        country_counts = df['customer_country'].value_counts()

        # Створення графіку
        ax = country_counts.plot(kind='bar')
        plt.title('Географічний розподіл замовлень')
        plt.xlabel('Країна')
        plt.ylabel('Кількість замовлень')

        # Додавання підписів
        for i, v in enumerate(country_counts):
            ax.text(i, v, str(v), ha='center', va='bottom')

        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        return self.save_plot_to_binary(plt.gcf(), 'geographic_distribution.png')

    def analyze_customer_relationship(self, df):
        """Аналіз впливу терміну співпраці з клієнтом"""
        fig, ax1 = plt.subplots(figsize=(12, 6))

        # Конвертуємо customer_relationship_days в числовий формат та переводимо в місяці
        df['relationship_months'] = pd.to_numeric(df['customer_relationship_days'], errors='coerce').fillna(0) / 30

        # Функція для категоризації терміну співпраці
        def get_relationship_category(months):
            if months < 2:
                return 'Нові'
            elif 2 <= months < 6:
                return '2-6 місяців'
            elif 6 <= months < 12:
                return '6-12 місяців'
            elif 12 <= months < 24:
                return '1-2 роки'
            else:
                return '2+ роки'

        # Визначаємо порядок категорій
        category_order = ['Нові', '2-6 місяців', '6-12 місяців', '1-2 роки', '2+ роки']

        # Застосовуємо категоризацію
        df['relationship_category'] = df['relationship_months'].apply(get_relationship_category)

        # Визначаємо успішність
        df['is_successful'] = df['state'] == 'sale'

        # Отримуємо останнє замовлення для кожного клієнта
        latest_orders = df.sort_values('date_order').groupby('customer_id').last()

        # Категоризуємо клієнтів на основі їх останнього замовлення
        latest_orders['relationship_category'] = latest_orders['relationship_months'].apply(get_relationship_category)

        # Рахуємо кількість клієнтів в кожній категорії
        category_counts = latest_orders['relationship_category'].value_counts()
        category_counts = category_counts.reindex(category_order)

        # Рахуємо кількість замовлень в кожній категорії
        orders_counts = df['relationship_category'].value_counts()
        orders_counts = orders_counts.reindex(category_order)

        # Рахуємо відсоток успішності для кожної категорії
        success_by_category = df.groupby('relationship_category')['is_successful'].mean()
        success_by_category = success_by_category.reindex(category_order)

        # Створюємо позиції для стовпчиків
        x = np.arange(len(category_counts))
        width = 0.35

        # Створюємо стовпчики для клієнтів (зліва від центру)
        bars1 = ax1.bar(x - width / 2, category_counts.values, width,
                        color='#1f77b4', label='Кількість клієнтів')
        ax1.set_xlabel('Термін співпраці')
        ax1.set_ylabel('Кількість клієнтів', color='#1f77b4')
        ax1.tick_params(axis='y', labelcolor='#1f77b4')

        # Створюємо другу вісь для замовлень
        ax3 = ax1.twinx()
        ax3.spines['right'].set_position(('outward', 60))
        bars2 = ax3.bar(x + width / 2, orders_counts.values, width,
                        color='skyblue', label='Кількість замовлень')
        ax3.set_ylabel('Кількість замовлень', color='blue')
        ax3.tick_params(axis='y', labelcolor='blue')

        # Створюємо третю вісь для відсотка успішності
        ax2 = ax1.twinx()
        success_line = ax2.plot(x, success_by_category.values * 100, 'o-',
                                color='gold', linewidth=2, markersize=8)
        ax2.set_ylabel('Відсоток успішності (%)', color='black')
        ax2.tick_params(axis='y', labelcolor='black')
        ax2.set_ylim(0, 100)

        # Налаштовуємо мітки осі X
        ax1.set_xticks(x)
        ax1.set_xticklabels(category_order, rotation=45)
        ax1.set_title('Розподіл клієнтів та замовлень відносно терміну співпраці')

        # Додаємо підписи значень для клієнтів
        for i, v in enumerate(category_counts.values):
            ax1.text(x[i] - width / 2, v, f'{int(v):,}',
                     ha='center', va='bottom', color='#1f77b4')

        # Додаємо підписи значень для замовлень
        for i, v in enumerate(orders_counts.values):
            ax3.text(x[i] + width / 2, v, f'{int(v):,}',
                     ha='center', va='bottom', color='blue')

        # Додаємо підписи для відсотка успішності
        for i, v in enumerate(success_by_category.values):
            ax2.text(i, v * 100 + 2, f'{v:.1%}',
                     ha='center', va='bottom', color='black')

        # Додаємо легенду
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2 = [Line2D([0], [0], color='gold', marker='o', linewidth=2, markersize=8)]
        lines3, labels3 = ax3.get_legend_handles_labels()

        ax1.legend(lines1 + lines3 + lines2,
                   ['Кількість клієнтів', 'Кількість замовлень', 'Відсоток успішності'],
                   loc='upper right')

        # Налаштування відступів
        plt.tight_layout()

        return self.save_plot_to_binary(fig, 'customer_relationship.png')

    def analyze_amount_correlation(self, df):
        """Аналіз впливу суми замовлення на успішність"""
        fig, ax1 = plt.subplots(figsize=(12, 6))

        # Конвертуємо суми в числовий формат
        df['total_amount'] = pd.to_numeric(df['total_amount'], errors='coerce').fillna(0)

        # Встановлюємо фіксовані межі для категорій (в тис. грн)
        bins = [float('-inf'), 500, 1000, 2000, 5000, float('inf')]
        labels = ['Дуже малі', 'Малі', 'Середні', 'Великі', 'Дуже великі']

        # Створення категорій сум замовлень
        df['amount_category'] = pd.cut(
            df['total_amount'],
            bins=bins,
            labels=labels,
            include_lowest=True
        )

        # Визначаємо успішність на основі state == 'sale'
        df['is_successful'] = df['state'] == 'sale'

        # Підрахунок кількості замовлень та успішності по категоріях
        category_counts = df['amount_category'].value_counts().reindex(labels)
        success_by_amount = df.groupby('amount_category')['is_successful'].mean().reindex(labels)

        # Створення графіку з двома осями
        x = np.arange(len(labels))
        bars = ax1.bar(x, category_counts.values, color='#1f77b4')
        ax1.set_xlabel('Категорія суми замовлення')
        ax1.set_ylabel('Кількість замовлень')

        # Додаємо другу вісь для відсотків
        ax2 = ax1.twinx()
        success_line = ax2.plot(x, success_by_amount.values * 100, 'o-', color='gold', linewidth=2, markersize=8)
        ax2.set_ylabel('Відсоток успішності (%)')
        ax2.set_ylim(0, 100)

        # Налаштовуємо мітки осі X
        ax1.set_xticks(x)
        ax1.set_xticklabels(labels, rotation=45)

        # Додаємо підписи значень
        for i, v in enumerate(category_counts.values):
            ax1.text(i, v, str(v), ha='center', va='bottom')

        for i, v in enumerate(success_by_amount.values):
            ax2.text(i, v * 100 + 2, f'{v:.1%}', ha='center', va='bottom', color='black')

        # Додаємо легенду

        custom_lines = [bars.patches[0], Line2D([0], [0], color='gold', marker='o', linewidth=2, markersize=8)]
        ax1.legend(custom_lines, ['Кількість замовлень', 'Відсоток успішності'], loc='upper right')

        # Додаємо інформацію про межі категорій
        info_text = 'Межі категорій:\n'
        info_text += f'Дуже малі: -inf - {bins[1]:,.2f}\n'
        info_text += f'Малі: {bins[1]:,.2f} - {bins[2]:,.2f}\n'
        info_text += f'Середні: {bins[2]:,.2f} - {bins[3]:,.2f}\n'
        info_text += f'Великі: {bins[3]:,.2f} - {bins[4]:,.2f}\n'
        info_text += f'Дуже великі: {bins[4]:,.2f} - inf'

        plt.figtext(1.02, 0.5, info_text, fontsize=8, va='center')

        plt.title('Успішність замовлень відносно суми')
        plt.tight_layout()

        return self.save_plot_to_binary(fig, 'amount_correlation.png')

    def analyze_product_lines(self, df):
        """Аналіз впливу кількості позицій в замовленні"""
        fig, ax1 = plt.subplots(figsize=(12, 6))

        # Конвертуємо кількість позицій в числовий формат
        df['order_lines_count'] = pd.to_numeric(df['order_lines_count'], errors='coerce').fillna(0)

        # Створюємо власні межі для категорій
        bins = [0, 2, 5, 10, 20, float('inf')]
        labels = ['1-2 позиції', '3-5 позицій', '6-10 позицій', '11-20 позицій', '20+ позицій']

        # Створення категорій кількості позицій
        df['lines_category'] = pd.cut(
            df['order_lines_count'],
            bins=bins,
            labels=labels,
            include_lowest=True
        )

        # Визначаємо успішність на основі state == 'sale'
        df['is_successful'] = df['state'] == 'sale'

        # Підрахунок кількості замовлень та успішності по категоріях
        category_counts = df['lines_category'].value_counts().reindex(labels)
        success_by_lines = df.groupby('lines_category')['is_successful'].mean().reindex(labels)

        # Створення графіку з двома осями
        x = np.arange(len(labels))
        bars = ax1.bar(x, category_counts.values, color='#1f77b4')
        ax1.set_xlabel('Кількість позицій')
        ax1.set_ylabel('Кількість замовлень')

        # Додаємо другу вісь для відсотків
        ax2 = ax1.twinx()
        success_line = ax2.plot(x, success_by_lines.values * 100, 'o-', color='gold', linewidth=2, markersize=8)
        ax2.set_ylabel('Відсоток успішності (%)')
        ax2.set_ylim(0, 100)

        # Налаштовуємо мітки осі X
        ax1.set_xticks(x)
        ax1.set_xticklabels(labels, rotation=45)

        # Додаємо підписи значень
        for i, v in enumerate(category_counts.values):
            ax1.text(i, v, str(v), ha='center', va='bottom')

        for i, v in enumerate(success_by_lines.values):
            ax2.text(i, v * 100 + 2, f'{v:.1%}', ha='center', va='bottom', color='black')

        # Додаємо легенду
        from matplotlib.lines import Line2D
        custom_lines = [bars.patches[0], Line2D([0], [0], color='gold', marker='o', linewidth=2, markersize=8)]
        ax1.legend(custom_lines, ['Кількість замовлень', 'Відсоток успішності'], loc='upper right')

        # Додаємо інформацію про межі категорій
        info_text = 'Межі категорій (кількість позицій):\n'
        info_text += f'1-2 позиції: {bins[0]} - {bins[1]}\n'
        info_text += f'3-5 позицій: {bins[1]} - {bins[2]}\n'
        info_text += f'6-10 позицій: {bins[2]} - {bins[3]}\n'
        info_text += f'11-20 позицій: {bins[3]} - {bins[4]}\n'
        info_text += f'20+ позицій: {bins[4]}+'

        plt.figtext(1.02, 0.5, info_text, fontsize=8, va='center')

        plt.title('Успішність замовлень відносно кількості позицій')
        plt.tight_layout()

        return self.save_plot_to_binary(fig, 'product_lines.png')

    def analyze_payment_methods(self, df):
        """Аналіз впливу методів оплати"""
        fig, ax1 = plt.subplots(figsize=(15, 8))

        # Підготовка даних про методи оплати
        payment_counts = df['payment_term'].value_counts()

        # Відбираємо топ-10 методів оплати за кількістю
        top_methods = payment_counts.nlargest(10)

        # Визначаємо успішність на основі state == 'sale'
        df['is_successful'] = df['state'] == 'sale'
        success_by_payment = df.groupby('payment_term')['is_successful'].mean()

        # Відбираємо успішність тільки для топ-10 методів
        success_filtered = success_by_payment[top_methods.index]

        # Створення графіку з двома осями
        x = np.arange(len(top_methods))
        bars = ax1.bar(x, top_methods.values, color='#1f77b4')
        ax1.set_xlabel('Метод оплати')
        ax1.set_ylabel('Кількість замовлень')

        # Додаємо другу вісь для відсотків
        ax2 = ax1.twinx()
        success_line = ax2.plot(x, success_filtered.values * 100, 'o-', color='gold', linewidth=2, markersize=8)
        ax2.set_ylabel('Відсоток успішності (%)')
        ax2.set_ylim(0, 100)

        # Налаштовуємо мітки осі X
        ax1.set_xticks(x)
        # Скорочуємо довгі назви методів оплати
        shortened_labels = [label.replace('Proforma', 'P.').replace('Invoice Date', 'Inv.').replace('Days From', 'D.F.')
                            for label in top_methods.index]
        ax1.set_xticklabels(shortened_labels, rotation=45, ha='right')

        # Додаємо підписи значень
        total_orders = len(df)
        for i, v in enumerate(top_methods.values):
            percentage = v / total_orders * 100
            ax1.text(i, v, f'{v}\n({percentage:.1f}%)', ha='center', va='bottom')

        for i, v in enumerate(success_filtered.values):
            ax2.text(i, v * 100 - 5, f'{v:.1%}', ha='center', va='bottom', color='black')

        # Додаємо легенду
        custom_lines = [bars.patches[0], Line2D([0], [0], color='gold', marker='o', linewidth=2, markersize=8)]
        ax1.legend(custom_lines, ['Кількість замовлень', 'Відсоток успішності'], loc='upper right')

        plt.title('Аналіз методів оплати (топ-10 за кількістю)')

        # Збільшуємо відступи знизу для довгих підписів
        plt.subplots_adjust(bottom=0.2)

        # Додаємо повну розшифровку скорочень
        legend_text = "Скорочення:\n" + "\n".join([f"{shortened}: {full}"
                                                   for shortened, full in zip(shortened_labels, top_methods.index)])
        plt.figtext(1.02, 0.5, legend_text, fontsize=8, va='center')

        plt.tight_layout()

        return self.save_plot_to_binary(fig, 'payment_methods.png')

    def analyze_delivery_methods(self, df):
        """Аналіз умов доставки"""
        fig, ax1 = plt.subplots(figsize=(15, 8))

        # Підготовка даних про методи доставки
        delivery_counts = df['delivery_method'].value_counts()
        total_orders = len(df)

        # Відбираємо топ-10 методів доставки за кількістю
        top_methods = delivery_counts.nlargest(10)

        # Визначаємо успішність на основі state == 'sale'
        df['is_successful'] = df['state'] == 'sale'
        success_by_delivery = df.groupby('delivery_method')['is_successful'].mean()

        # Відбираємо успішність тільки для топ-10 методів
        success_filtered = success_by_delivery[top_methods.index]

        # Створення графіку з двома осями
        x = np.arange(len(top_methods))
        bars = ax1.bar(x, top_methods.values, color='#1f77b4')
        ax1.set_xlabel('Метод доставки')
        ax1.set_ylabel('Кількість замовлень')

        # Додаємо другу вісь для відсотків
        ax2 = ax1.twinx()
        success_line = ax2.plot(x, success_filtered.values * 100, 'o-', color='gold', linewidth=2, markersize=8)
        ax2.set_ylabel('Відсоток успішності (%)')
        ax2.set_ylim(0, 100)

        # Налаштовуємо мітки осі X
        ax1.set_xticks(x)
        # Скорочуємо довгі назви методів доставки
        shortened_labels = []
        for label in top_methods.index:
            shortened = label
            if len(label) > 20:
                words = label.split()
                shortened = ' '.join(w[:3] + '.' if len(w) > 3 else w for w in words)
            shortened_labels.append(shortened)

        ax1.set_xticklabels(shortened_labels, rotation=45, ha='right')

        # Додаємо підписи значень
        for i, v in enumerate(top_methods.values):
            percentage = v / total_orders * 100
            ax1.text(i, v, f'{v}\n({percentage:.1f}%)', ha='center', va='bottom')

        for i, v in enumerate(success_filtered.values):
            ax2.text(i, v * 100 - 5, f'{v:.1%}', ha='center', va='bottom', color='black')

        # Додаємо легенду
        custom_lines = [bars.patches[0], Line2D([0], [0], color='gold', marker='o', linewidth=2, markersize=8)]
        ax1.legend(custom_lines, ['Кількість замовлень', 'Відсоток успішності'], loc='upper right')

        plt.title('Аналіз методів доставки (топ-10 за кількістю)')

        # Збільшуємо відступи знизу для довгих підписів
        plt.subplots_adjust(bottom=0.2)

        # Додаємо повну розшифровку скорочень, якщо були скорочення
        if any(l != o for l, o in zip(shortened_labels, top_methods.index)):
            legend_text = "Повні назви:\n" + "\n".join([f"{shortened}: {full}"
                                                        for shortened, full in zip(shortened_labels, top_methods.index)
                                                        if shortened != full])
            plt.figtext(1.02, 0.5, legend_text, fontsize=8, va='center')

        plt.tight_layout()

        return self.save_plot_to_binary(fig, 'delivery_methods.png')

    def analyze_changes_impact(self, df):
        """Аналіз впливу змін на успішність замовлення"""
        fig, ax1 = plt.subplots(figsize=(15, 8))

        # Підготовка даних про зміни в замовленнях
        changes_counts = df['changes_count'].value_counts()
        total_orders = len(df)

        # Конвертуємо індекс в числа для правильного сортування
        changes_counts.index = changes_counts.index.astype(int)

        # Відбираємо значення, де кількість замовлень більше 100 (для читабельності)
        significant_changes = changes_counts[changes_counts >= 100]
        # Сортуємо за числовим індексом
        significant_changes = significant_changes.sort_index()

        # Визначаємо успішність на основі state == 'sale'
        df['is_successful'] = df['state'] == 'sale'
        success_by_changes = df.groupby('changes_count')['is_successful'].mean()
        # Конвертуємо індекс в числа для правильного сортування
        success_by_changes.index = success_by_changes.index.astype(int)

        # Відбираємо успішність тільки для значущих змін
        success_filtered = success_by_changes[significant_changes.index]

        # Створення графіку з двома осями
        x = np.arange(len(significant_changes))
        bars = ax1.bar(x, significant_changes.values, color='#1f77b4')
        ax1.set_xlabel('Кількість змін')
        ax1.set_ylabel('Кількість замовлень')

        # Додаємо другу вісь для відсотків
        ax2 = ax1.twinx()
        success_line = ax2.plot(x, success_filtered.values * 100, 'o-', color='gold', linewidth=2, markersize=8)
        ax2.set_ylabel('Відсоток успішності (%)')
        ax2.set_ylim(0, 100)

        # Налаштовуємо мітки осі X
        ax1.set_xticks(x)
        ax1.set_xticklabels(significant_changes.index, rotation=0)

        # Додаємо підписи значень
        for i, v in enumerate(significant_changes.values):
            percentage = v / total_orders * 100
            ax1.text(i, v, f'{v}\n({percentage:.1f}%)', ha='center', va='bottom')

        for i, v in enumerate(success_filtered.values):
            ax2.text(i, v * 100 + 2, f'{v:.1%}', ha='center', va='bottom', color='black')

        # Додаємо легенду
        from matplotlib.lines import Line2D
        custom_lines = [bars.patches[0], Line2D([0], [0], color='gold', marker='o', linewidth=2, markersize=8)]
        ax1.legend(custom_lines, ['Кількість замовлень', 'Відсоток успішності'], loc='upper right')

        plt.title('Аналіз впливу змін на замовлення\n(показано категорії з кількістю замовлень ≥ 100)')

        # Додаємо інформацію про відфільтровані дані
        filtered_orders = changes_counts[changes_counts < 100].sum()
        filtered_percentage = filtered_orders / total_orders * 100
        info_text = f"Відфільтровано:\n{filtered_orders:,} замовлень ({filtered_percentage:.1f}%)\nз {len(changes_counts) - len(significant_changes)} категорій\nз меншою кількістю замовлень"
        plt.figtext(1.02, 0.5, info_text, fontsize=8, va='center')

        plt.tight_layout()

        return self.save_plot_to_binary(fig, 'changes_impact.png')

    def analyze_communication(self, df):
        """Аналіз впливу комунікацій на успішність"""
        fig, ax1 = plt.subplots(figsize=(15, 8))

        # Підготовка даних про комунікації
        df['messages_count'] = pd.to_numeric(df['messages_count'], errors='coerce').fillna(0)

        # Створюємо межі для категорій
        message_bins = [-1, 0, 3, 7, 15, float('inf')]
        message_labels = ['Без повідомлень', '1-3 повідомлення', '4-7 повідомлень', '8-15 повідомлень',
                          '15+ повідомлень']

        df['message_category'] = pd.cut(
            df['messages_count'],
            bins=message_bins,
            labels=message_labels,
            include_lowest=True
        )

        # Підрахунок замовлень по кількості повідомлень
        message_counts = df['message_category'].value_counts().sort_index()
        total_orders = len(df)

        # Визначаємо успішність на основі state == 'sale'
        df['is_successful'] = df['state'] == 'sale'
        success_by_messages = df.groupby('message_category')['is_successful'].mean()

        # Створення графіку з двома осями
        x = np.arange(len(message_counts))
        bars = ax1.bar(x, message_counts.values, color='#1f77b4')
        ax1.set_xlabel('Кількість повідомлень')
        ax1.set_ylabel('Кількість замовлень')

        # Додаємо другу вісь для відсотків
        ax2 = ax1.twinx()
        success_line = ax2.plot(x, success_by_messages.values * 100, 'o-', color='gold', linewidth=2, markersize=8)
        ax2.set_ylabel('Відсоток успішності (%)')
        ax2.set_ylim(0, 100)

        # Налаштовуємо мітки осі X
        ax1.set_xticks(x)
        ax1.set_xticklabels(message_counts.index, rotation=45, ha='right')

        # Додаємо підписи значень
        for i, v in enumerate(message_counts.values):
            percentage = v / total_orders * 100
            ax1.text(i, v, f'{v}\n({percentage:.1f}%)', ha='center', va='bottom')

        for i, v in enumerate(success_by_messages.values):
            ax2.text(i, v * 100 - 3, f'{v:.1%}', ha='center', va='bottom', color='black')

        # Додаємо легенду
        from matplotlib.lines import Line2D
        custom_lines = [bars.patches[0], Line2D([0], [0], color='gold', marker='o', linewidth=2, markersize=8)]
        ax1.legend(custom_lines, ['Кількість замовлень', 'Відсоток успішності'], loc='upper right')

        plt.title('Аналіз впливу комунікацій на замовлення')

        # Додаємо інформацію про межі категорій
        info_text = "Межі категорій (кількість повідомлень):\n" + "\n".join([
            f'{message_labels[i]}: {message_bins[i] + 1 if i > 0 else 0} - {message_bins[i + 1] if message_bins[i + 1] != float("inf") else "inf"}'
            for i in range(len(message_labels))
        ])
        plt.figtext(1.02, 0.5, info_text, fontsize=8, va='center')

        # Збільшуємо відступи знизу для довгих підписів та справа для легенди
        plt.subplots_adjust(bottom=0.2, right=0.85)

        return self.save_plot_to_binary(fig, 'communication_analysis.png')

    def analyze_manager_performance(self, df):
        """Аналіз ефективності менеджерів"""
        fig, ax1 = plt.subplots(figsize=(15, 8))

        # Підготовка даних про менеджерів
        manager_counts = df['salesperson'].value_counts()
        total_orders = len(df)

        # Відбираємо топ-10 менеджерів за кількістю замовлень
        top_managers = manager_counts.nlargest(10)

        # Визначаємо успішність на основі state == 'sale'
        df['is_successful'] = df['state'] == 'sale'
        success_by_manager = df.groupby('salesperson')['is_successful'].mean()
        success_filtered = success_by_manager[top_managers.index]

        # Створення графіку з двома осями
        x = np.arange(len(top_managers))
        bars = ax1.bar(x, top_managers.values, color='#1f77b4')
        ax1.set_xlabel('Менеджер')
        ax1.set_ylabel('Кількість замовлень')

        # Додаємо другу вісь для відсотків
        ax2 = ax1.twinx()
        success_line = ax2.plot(x, success_filtered.values * 100, 'o-',
                                color='gold', linewidth=2, markersize=8)
        ax2.set_ylabel('Відсоток успішності (%)')
        ax2.set_ylim(0, 100)

        # Налаштовуємо мітки осі X
        ax1.set_xticks(x)
        ax1.set_xticklabels(top_managers.index, rotation=45, ha='right')

        # Додаємо підписи значень
        for i, v in enumerate(top_managers.values):
            percentage = v / total_orders * 100
            ax1.text(i, v, f'{v}\n({percentage:.1f}%)', ha='center', va='bottom')

        for i, v in enumerate(success_filtered.values):
            ax2.text(i, v * 100 + 2, f'{v:.1%}', ha='center', va='bottom', color='black')

        # Додаємо легенду
        from matplotlib.lines import Line2D
        custom_lines = [bars.patches[0], Line2D([0], [0], color='gold', marker='o',
                                                linewidth=2, markersize=8)]
        ax1.legend(custom_lines, ['Кількість замовлень', 'Відсоток успішності'],
                   loc='upper right')

        plt.title('Аналіз ефективності менеджерів\n(топ-10 за кількістю замовлень)')

        # Додаємо інформацію про відфільтровані дані
        filtered_orders = manager_counts[~manager_counts.index.isin(top_managers.index)].sum()
        filtered_percentage = filtered_orders / total_orders * 100
        info_text = (f"Відфільтровано:\n{filtered_orders:,} замовлень "
                     f"({filtered_percentage:.1f}%)\nвід "
                     f"{len(manager_counts) - len(top_managers)} менеджерів\n"
                     f"з меншою кількістю замовлень")
        plt.figtext(1.02, 0.5, info_text, fontsize=8, va='center')

        # Збільшуємо відступи знизу для довгих підписів та справа для легенди
        plt.subplots_adjust(bottom=0.2, right=0.85)

        return self.save_plot_to_binary(fig, 'manager_performance.png')

    def generate_analysis(self):
        """Генерує всі графіки аналізу"""
        # Отримання даних

        data = self._read_csv_extended_data()
        df = pd.DataFrame(data)

        # Перевірка на коректність даних у колонці processing_time_hours
        df['processing_time_hours'] = pd.to_numeric(df['processing_time_hours'], errors='coerce')

        # Виведення некоректних даних
        invalid_data = df[df['processing_time_hours'].isna()]
        if not invalid_data.empty:
            print("Некоректні дані в колонці 'processing_time_hours':")
            print(invalid_data[['order_id', 'processing_time_hours']].to_string(index=False))

        # Перевірка та конвертація даних у колонці discount_total
        df['discount_total'] = pd.to_numeric(df['discount_total'], errors='coerce')

        # Виведення некоректних даних
        invalid_data = df[df['discount_total'].isna()]
        if not invalid_data.empty:
            print("Некоректні дані в колонці 'discount_total':")
            print(invalid_data[['order_id', 'discount_total']].to_string(index=False))

        # Заміна некоректних значень на 0
        df['discount_total'] = df['discount_total'].fillna(0)

        # Збереження базової статистики
        self.total_orders = len(df)
        df['is_successful'] = df['state'].apply(lambda x: 1 if x == 'sale' else 0)
        self.success_rate = (df['is_successful'].mean() * 100)
        df['create_date'] = pd.to_datetime(df['create_date'])
        df['date_order'] = pd.to_datetime(df['date_order'])
        df['avg_response_time_days'] = abs((df['date_order'] - df['create_date']).dt.total_seconds() / (3600 * 24))
        self.avg_response_time = df['avg_response_time_days'].mean()
        self.avg_processing_time = df['processing_time_hours'].mean()

        # Генерація графіків
        discount_analysis_binary,discount_analysis_filename = self.analyze_discounts(df)
        if discount_analysis_binary:
            self.discount_analysis_graph = discount_analysis_binary
            self.discount_analysis_graph_filename = discount_analysis_filename

        time_distribution_binary, time_distribution_filename = self.analyze_time_distribution(df)
        if time_distribution_binary:
            self.time_distribution_graph = time_distribution_binary
            self.time_distribution_filename = time_distribution_filename

        seasonal_monthly_binary, seasonal_monthly_filename = self.analyze_seasonal_monthly(df)
        if seasonal_monthly_binary:
            self.seasonal_monthly_graph = seasonal_monthly_binary
            self.seasonal_monthly_filename = seasonal_monthly_filename

        seasonal_weekday_binary, seasonal_weekday_filename = self.analyze_seasonal_weekday(df)
        if seasonal_weekday_binary:
            self.seasonal_weekday_graph = seasonal_weekday_binary
            self.seasonal_weekday_filename = seasonal_weekday_filename

        processing_duration_binary, processing_duration_filename = self.analyze_processing_duration(df)
        if processing_duration_binary:
            self.processing_duration_graph = processing_duration_binary
            self.processing_duration_filename = processing_duration_filename

        customer_history_binary, customer_history_filename = self.analyze_customer_history(df)
        if customer_history_binary:
            self.customer_history_graph = customer_history_binary
            self.customer_history_filename = customer_history_filename

        customer_relationship_binary, customer_relationship_filename = self.analyze_customer_relationship(df)
        if customer_relationship_binary:
            self.customer_relationship_graph = customer_relationship_binary
            self.customer_relationship_filename = customer_relationship_filename

        amount_correlation_binary, amount_correlation_filename = self.analyze_amount_correlation(df)
        if amount_correlation_binary:
            self.amount_correlation_graph = amount_correlation_binary
            self.amount_correlation_filename = amount_correlation_filename

        product_lines_binary, product_lines_filename = self.analyze_product_lines(df)
        if product_lines_binary:
            self.product_lines_graph = product_lines_binary
            self.product_lines_filename = product_lines_filename

        payment_analysis_binary, payment_analysis_filename = self.analyze_payment_methods(df)
        if payment_analysis_binary:
            self.payment_analysis_graph = payment_analysis_binary
            self.payment_analysis_filename = payment_analysis_filename

        delivery_analysis_binary, delivery_analysis_filename = self.analyze_delivery_methods(df)
        if delivery_analysis_binary:
            self.delivery_analysis_graph = delivery_analysis_binary
            self.delivery_analysis_filename = delivery_analysis_filename

        changes_impact_binary, changes_impact_filename = self.analyze_changes_impact(df)
        if changes_impact_binary:
            self.changes_impact_graph = changes_impact_binary
            self.changes_impact_filename = changes_impact_filename

        communication_analysis_binary, communication_analysis_filename = self.analyze_communication(df)
        if communication_analysis_binary:
            self.communication_analysis_graph = communication_analysis_binary
            self.communication_analysis_filename = communication_analysis_filename

        customer_avg_messages_result = self.analyze_customer_avg_messages(df)
        if customer_avg_messages_result:
            self.customer_avg_messages_graph, self.customer_avg_messages_filename = customer_avg_messages_result

        customer_avg_changes_result = self.analyze_customer_avg_changes(df)
        if customer_avg_messages_result:
            self.customer_avg_changes_graph, self.customer_avg_changes_filename  = customer_avg_changes_result

        manager_performance_binary, manager_performance_filename = self.analyze_manager_performance(df)
        if manager_performance_binary:
            self.manager_performance_graph = manager_performance_binary
            self.manager_performance_filename = manager_performance_filename

        customer_relationship_distribution_binary, customer_relationship_distribution_filename = self.analyze_customer_relationship_distribution(df)
        if customer_relationship_distribution_binary:
            self.customer_relationship_distribution_graph = customer_relationship_distribution_binary
            self.customer_relationship_distribution_filename = customer_relationship_distribution_filename

        customer_amount_success_distribution = self.analyze_customer_amount_success_distribution(df)
        if customer_amount_success_distribution:
            self.customer_amount_success_distribution_graph = customer_amount_success_distribution
        self.changes_messages_correlation_graph, self.changes_messages_correlation_filename = self.analyze_changes_messages_correlation(df)

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
            self.action_compute_and_draw()
            self.action_compute_salesperson_chart()

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
                record.avg_amount_success_chart = False
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

                record.avg_amount_success_chart = record._create_amount_based_chart(
                    partner_stats, 'avg_amount',
                    'Success Rate by Average Order Amount',
                    'Average Order Amount'
                )
            except Exception as e:
                print(f"Error computing amount success charts: {str(e)}")
                record.avg_amount_success_chart = False

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

    def analyze_customer_avg_messages(self, df):
        """Аналіз клієнтів за середньою кількістю повідомлень в замовленнях"""
        fig, ax1 = plt.subplots(figsize=(12, 6))

        # Конвертуємо messages_count в числовий формат
        df['messages_count'] = pd.to_numeric(df['messages_count'], errors='coerce').fillna(0)

        # Рахуємо середню кількість повідомлень для кожного клієнта
        customer_stats = df.groupby('customer_id').agg({
            'messages_count': 'mean',  # середня кількість повідомлень
            'order_id': 'count',  # кількість замовлень
            'state': lambda x: (x == 'sale').mean()  # відсоток успішності
        }).reset_index()

        # Замінюємо NaN на 0
        customer_stats = customer_stats.fillna(0)

        # Функція категоризації
        def get_message_category(avg_messages):
            if pd.isna(avg_messages) or avg_messages == 0:
                return 'Без повідомлень'
            elif 0 < avg_messages <= 3:
                return '1-3 повідомлення'
            elif 3 < avg_messages <= 7:
                return '4-7 повідомлень'
            elif 7 < avg_messages <= 15:
                return '8-15 повідомлень'
            else:
                return '15+ повідомлень'

        # Визначаємо порядок категорій
        category_order = ['Без повідомлень', '1-3 повідомлення', '4-7 повідомлень',
                          '8-15 повідомлень', '15+ повідомлень']

        # Категоризуємо клієнтів
        customer_stats['message_category'] = customer_stats['messages_count'].apply(get_message_category)

        # Рахуємо статистику по категоріях
        category_stats = customer_stats.groupby('message_category').agg({
            'customer_id': 'count',  # кількість клієнтів
            'order_id': 'sum',  # кількість замовлень
            'state': 'mean'  # середній відсоток успішності
        }).reindex(category_order)

        # Замінюємо NaN на 0
        category_stats = category_stats.fillna(0)

        # Створюємо позиції для стовпчиків
        x = np.arange(len(category_order))
        width = 0.35

        # Створюємо стовпчики для клієнтів
        bars1 = ax1.bar(x - width / 2, category_stats['customer_id'], width,
                        color='#1f77b4', label='Кількість клієнтів')
        ax1.set_ylabel('Кількість клієнтів', color='#1f77b4')
        ax1.tick_params(axis='y', labelcolor='#1f77b4')

        # Створюємо другу вісь для замовлень
        ax3 = ax1.twinx()
        ax3.spines['right'].set_position(('outward', 60))
        bars2 = ax3.bar(x + width / 2, category_stats['order_id'], width,
                        color='skyblue', label='Кількість замовлень')
        ax3.set_ylabel('Кількість замовлень', color='blue')
        ax3.tick_params(axis='y', labelcolor='blue')

        # Створюємо третю вісь для відсотка успішності
        ax2 = ax1.twinx()
        success_line = ax2.plot(x, category_stats['state'] * 100, 'o-',
                                color='gold', linewidth=2, markersize=8,
                                label='Відсоток успішності')
        ax2.set_ylabel('Відсоток успішності (%)')
        ax2.set_ylim(0, 100)

        # Налаштовуємо мітки осі X
        ax1.set_xticks(x)
        ax1.set_xticklabels(category_order, rotation=45, ha='right')

        # Додаємо підписи значень для клієнтів
        for i, v in enumerate(category_stats['customer_id']):
            if not pd.isna(v):  # перевіряємо на NaN
                ax1.text(x[i] - width / 2, v, f'{int(v):,}',
                         ha='center', va='bottom', color='#1f77b4')

        # Додаємо підписи значень для замовлень
        for i, v in enumerate(category_stats['order_id']):
            if not pd.isna(v):  # перевіряємо на NaN
                ax3.text(x[i] + width / 2, v, f'{int(v):,}',
                         ha='center', va='bottom', color='blue')

        # Додаємо підписи для відсотка успішності
        for i, v in enumerate(category_stats['state']):
            if not pd.isna(v):  # перевіряємо на NaN
                ax2.text(x[i], v * 100 + 1, f'{v:.1%}',
                         ha='center', va='bottom', color='black')

        # Налаштовуємо заголовок та легенду
        plt.title('Розподіл клієнтів та замовлень за середньою кількістю повідомлень')

        # Збільшуємо відступи
        plt.subplots_adjust(bottom=0.15, right=0.85)

        return self.save_plot_to_binary(fig, 'customer_avg_messages.png')

    def analyze_customer_avg_changes(self, df):
        """Analysis of customers by average number of changes in their orders"""
        fig, ax1 = plt.subplots(figsize=(15, 8))

        # Переконуємося, що changes_count є числовим
        df['changes_count'] = pd.to_numeric(df['changes_count'], errors='coerce').fillna(0)

        # Додамо додатковий друк для діагностики
        print("Unique states:", df['state'].unique())
        print("Changes count dtype:", df['changes_count'].dtype)

        # Розрахунок середньої кількості змін для кожного клієнта
        customer_changes = df.groupby('customer_id').agg({
            'changes_count': 'mean',
            'state': lambda x: (x == 'sale').astype(float).mean()  # Явно конвертуємо у float
        }).reset_index()

        # Створення категорій на основі середньої кількості змін
        def get_changes_category(changes):
            if changes == 0:
                return 'Без змін'
            elif changes <= 2:
                return '1-2 зміни'
            elif changes <= 5:
                return '3-5 змін'
            elif changes <= 10:
                return '6-10 змін'
            else:
                return '10+ змін'

        customer_changes['category'] = customer_changes['changes_count'].apply(get_changes_category)

        # Агрегація даних за категоріями
        category_stats = customer_changes.groupby('category').agg({
            'customer_id': 'count',
            'changes_count': 'mean',
            'state': 'mean'
        }).reset_index()

        # Сортування категорій у правильному порядку
        category_order = ['Без змін', '1-2 зміни', '3-5 змін', '6-10 змін', '10+ змін']
        category_stats['category'] = pd.Categorical(category_stats['category'],
                                                    categories=category_order,
                                                    ordered=True)
        category_stats = category_stats.sort_values('category')

        # Створення графіку
        x = np.arange(len(category_stats))
        bars = ax1.bar(x, category_stats['customer_id'], color='#1f77b4')
        ax1.set_xlabel('Категорії за кількістю змін')
        ax1.set_ylabel('Кількість клієнтів')

        # Додаємо другу вісь для відсотків
        ax2 = ax1.twinx()
        success_line = ax2.plot(x, category_stats['state'] * 100, 'o-',
                                color='gold', linewidth=2, markersize=8)
        ax2.set_ylabel('Відсоток успішності (%)')
        ax2.set_ylim(0, 100)

        # Налаштовуємо мітки осі X
        ax1.set_xticks(x)
        ax1.set_xticklabels(category_stats['category'], rotation=45)

        # Додаємо підписи значень
        total_customers = category_stats['customer_id'].sum()
        for i, v in enumerate(category_stats['customer_id']):
            percentage = v / total_customers * 100
            ax1.text(i, v, f'{v}\n({percentage:.1f}%)', ha='center', va='bottom')

        for i, v in enumerate(category_stats['state']):
            ax2.text(i, v * 100 + 2, f'{v:.1%}', ha='center', va='bottom', color='black')

        # Додаємо середню кількість змін для кожної категорії
        for i, avg_changes in enumerate(category_stats['changes_count']):
            ax1.text(i, 0, f'~{avg_changes:.1f}', ha='center', va='top')

        # Додаємо легенду
        custom_lines = [bars.patches[0], Line2D([0], [0], color='gold', marker='o', linewidth=2, markersize=8)]
        ax1.legend(custom_lines, ['Кількість клієнтів', 'Відсоток успішності'], loc='upper right')

        plt.title('Аналіз клієнтів за середньою кількістю змін в замовленнях')
        plt.tight_layout()

        return self.save_plot_to_binary(fig, 'customer_avg_changes.png')

    def analyze_changes_messages_correlation(self, df):
        """Analysis of correlation between number of changes and messages in orders"""
        fig, ax = plt.subplots(figsize=(15, 8))

        # Переконуємося, що дані числові
        df['changes_count'] = pd.to_numeric(df['changes_count'], errors='coerce').fillna(0)
        df['messages_count'] = pd.to_numeric(df['messages_count'], errors='coerce').fillna(0)

        # Створюємо копію даних для аналізу
        analysis_df = df[['changes_count', 'messages_count', 'state']].copy()

        # Створюємо 10 груп з приблизно однаковою кількістю замовлень
        analysis_df['message_group'] = pd.qcut(analysis_df['messages_count'],
                                               q=10,
                                               duplicates='drop')

        # Створюємо зрозумілі лейбли для груп
        def format_range(interval):
            left = int(interval.left)
            right = int(interval.right)
            return f'{left}-{right}'

        # Отримуємо межі інтервалів та створюємо нові лейбли
        intervals = analysis_df['message_group'].cat.categories
        labels = [format_range(interval) for interval in intervals]

        # Застосовуємо нові лейбли
        analysis_df['message_group'] = pd.qcut(analysis_df['messages_count'],
                                               q=10,
                                               labels=labels,
                                               duplicates='drop')

        # Рахуємо статистику для кожної групи
        group_stats = analysis_df.groupby('message_group').agg({
            'messages_count': ['mean', 'count'],
            'changes_count': 'mean',
            'state': lambda x: (x == 'sale').mean()
        }).reset_index()

        # Спрощуємо мультиіндекс колонок
        group_stats.columns = ['group', 'avg_messages', 'orders_count', 'avg_changes', 'success_rate']

        # Додамо діагностичний друк статистики груп
        print("\nGroup statistics:")
        print(group_stats)

        # Створення графіку з двома осями
        x = np.arange(len(group_stats))

        # Основні стовпці - середня кількість змін
        bars = ax.bar(x, group_stats['avg_changes'], color='#1f77b4', alpha=0.7)
        ax.set_xlabel('Групи замовлень за кількістю повідомлень')
        ax.set_ylabel('Середня кількість змін', color='#1f77b4')
        ax.tick_params(axis='y', labelcolor='#1f77b4')

        # Додаємо другу вісь для успішності
        ax2 = ax.twinx()
        success_line = ax2.plot(x, group_stats['success_rate'] * 100, 'o-',
                                color='gold', linewidth=2, markersize=8)
        ax2.set_ylabel('Відсоток успішності (%)', color='gold')
        ax2.tick_params(axis='y', labelcolor='gold')
        ax2.set_ylim(0, 100)

        # Налаштовуємо мітки осі X
        ax.set_xticks(x)
        ax.set_xticklabels(group_stats['group'], rotation=45)

        # Додаємо підписи значень
        for i, (changes, messages, count) in enumerate(zip(group_stats['avg_changes'],
                                                           group_stats['avg_messages'],
                                                           group_stats['orders_count'])):
            # Підпис середньої кількості змін
            ax.text(i, changes, f'~{changes:.1f}',
                    ha='center', va='bottom', color='#1f77b4')
            # Підпис кількості замовлень
            ax.text(i, 0, f'n={count}',
                    ha='center', va='top', color='gray')

        # Додаємо підписи успішності
        for i, success in enumerate(group_stats['success_rate']):
            ax2.text(i, success * 100 + 2, f'{success:.1%}',
                     ha='center', va='bottom', color='black')

        # Додаємо легенду
        custom_lines = [bars.patches[0], Line2D([0], [0], color='gold', marker='o', linewidth=2, markersize=8)]
        ax.legend(custom_lines, ['Середня кількість змін', 'Відсоток успішності'], loc='upper left')

        plt.title('Залежність кількості змін від кількості повідомлень в замовленнях')
        plt.tight_layout()

        return self.save_plot_to_binary(fig, 'changes_messages_correlation.png')

    def analyze_customer_relationship_distribution(self, df):
        """Analysis of orders distribution by customer relationship duration"""
        fig, ax = plt.subplots(figsize=(15, 8))

        # Конвертуємо дні в місяці та забезпечуємо числовий формат
        df['relationship_months'] = pd.to_numeric(df['customer_relationship_days'],
                                                  errors='coerce').fillna(0) / 30

        # Отримуємо останнє замовлення для кожного клієнта
        latest_orders = df.sort_values('date_order').groupby('customer_id').last()

        # Додамо діагностичний друк
        print("Unique relationship months:", sorted(latest_orders['relationship_months'].unique()))

        # Створюємо власні межі для груп на основі процентилів
        percentiles = np.percentile(latest_orders['relationship_months'].unique(),
                                    np.linspace(0, 100, 11))  # 11 точок для 10 інтервалів

        # Переконуємося, що межі унікальні
        percentiles = np.unique(percentiles)
        if len(percentiles) < 11:
            # Якщо у нас менше унікальних значень, додаємо невеликі відступи
            missing = 11 - len(percentiles)
            step = (percentiles[-1] - percentiles[0]) / (10 * 100)
            for i in range(missing):
                percentiles = np.insert(percentiles, -1, percentiles[-1] + step)

        def format_duration(months):
            months = int(months)
            if months < 12:
                return f"{months}м"
            years = months // 12
            months = months % 12
            if months == 0:
                return f"{years}р"
            return f"{years}р {months}м"

        # Створюємо групи з унікальними межами
        labels = [f"{format_duration(left)}-{format_duration(right)}"
                  for left, right in zip(percentiles[:-1], percentiles[1:])]

        latest_orders['relationship_group'] = pd.cut(latest_orders['relationship_months'],
                                                     bins=percentiles,
                                                     labels=labels,
                                                     include_lowest=True)

        # Додаємо групи до основного датафрейму
        customer_groups = latest_orders[['relationship_group']].copy()
        df = df.merge(customer_groups,
                      left_on='customer_id',
                      right_index=True,
                      how='left')

        # Рахуємо статистику для кожної групи
        group_stats = df.groupby('relationship_group').agg({
            'customer_id': [
                ('customers', 'nunique'),  # кількість унікальних клієнтів
                ('orders', 'count')  # кількість замовлень
            ],
            'state': lambda x: (x == 'sale').mean()  # успішність
        }).reset_index()

        # Спрощуємо мультиіндекс колонок
        group_stats.columns = ['group', 'customers', 'orders', 'success_rate']

        # Додаємо середню кількість замовлень на клієнта
        group_stats['avg_orders'] = group_stats['orders'] / group_stats['customers']

        # Створення графіку з двома осями
        x = np.arange(len(group_stats))

        # Основні стовпці - середня кількість замовлень на клієнта
        bars = ax.bar(x, group_stats['avg_orders'], color='#1f77b4', alpha=0.7)
        ax.set_xlabel('Тривалість співпраці з клієнтом')
        ax.set_ylabel('Середня кількість замовлень на клієнта', color='#1f77b4')
        ax.tick_params(axis='y', labelcolor='#1f77b4')

        # Додаємо другу вісь для успішності
        ax2 = ax.twinx()
        success_line = ax2.plot(x, group_stats['success_rate'] * 100, 'o-',
                                color='gold', linewidth=2, markersize=8)
        ax2.set_ylabel('Відсоток успішності (%)', color='gold')
        ax2.tick_params(axis='y', labelcolor='gold')
        ax2.set_ylim(0, 100)

        # Налаштовуємо мітки осі X
        ax.set_xticks(x)
        ax.set_xticklabels(group_stats['group'], rotation=45)

        # Додаємо підписи значень
        for i, (avg_orders, customers, orders) in enumerate(zip(group_stats['avg_orders'],
                                                                group_stats['customers'],
                                                                group_stats['orders'])):
            # Підпис середньої кількості замовлень
            ax.text(i, avg_orders, f'~{avg_orders:.1f}',
                    ha='center', va='bottom', color='#1f77b4')
            # Підпис кількості клієнтів та замовлень
            ax.text(i, 0, f'n={customers}\n({orders})',
                    ha='center', va='top', color='gray')

        # Додаємо підписи успішності
        for i, success in enumerate(group_stats['success_rate']):
            ax2.text(i, success * 100 + 2, f'{success:.1%}',
                     ha='center', va='bottom', color='black')

        # Додаємо легенду
        custom_lines = [bars.patches[0], Line2D([0], [0], color='gold', marker='o', linewidth=2, markersize=8)]
        ax.legend(custom_lines, ['Середня кількість замовлень', 'Відсоток успішності'], loc='upper left')

        plt.title('Залежність кількості замовлень від тривалості співпраці з клієнтом')
        plt.tight_layout()

        return self.save_plot_to_binary(fig, 'customer_relationship_distribution.png')

        # Налаштовуємо мітки осі X
        ax.set_xticks(x)
        ax.set_xticklabels(group_stats['group'], rotation=45)

        # Додаємо підписи значень
        for i, (avg_orders, customers, orders) in enumerate(zip(group_stats['avg_orders'],
                                                                group_stats['customers'],
                                                                group_stats['orders'])):
            # Підпис середньої кількості замовлень
            ax.text(i, avg_orders, f'~{avg_orders:.1f}',
                    ha='center', va='bottom', color='#1f77b4')
            # Підпис кількості клієнтів та замовлень
            ax.text(i, 0, f'n={customers}\n({orders})',
                    ha='center', va='top', color='gray')

        # Додаємо підписи успішності
        for i, success in enumerate(group_stats['success_rate']):
            ax2.text(i, success * 100 + 2, f'{success:.1%}',
                     ha='center', va='bottom', color='black')

        # Додаємо легенду
        custom_lines = [bars.patches[0], Line2D([0], [0], color='gold', marker='o', linewidth=2, markersize=8)]
        ax.legend(custom_lines, ['Середня кількість замовлень', 'Відсоток успішності'], loc='upper left')

        plt.title('Залежність кількості замовлень від тривалості співпраці з клієнтом')
        plt.tight_layout()

        return self.save_plot_to_binary(fig, 'customer_relationship_distribution.png')

    def analyze_customer_amount_success_distribution(self, df):
        """Analysis of success rate distribution by average order amount"""
        try:
            print("\n=== Starting analysis ===")

            # Закриваємо всі відкриті фігури перед створенням нової
            plt.close('all')

            fig, ax = plt.subplots(figsize=(15, 8))

            # Конвертуємо суму в числовий формат
            df['total_amount'] = pd.to_numeric(df['total_amount'], errors='coerce')

            # Відфільтруємо від'ємні значення
            df = df[df['total_amount'] >= 0]

            # Розраховуємо середню суму замовлень для кожного клієнта
            customer_stats = df.groupby('customer_id').agg({
                'total_amount': 'mean',
                'state': lambda x: (x == 'sale').mean() * 100  # відсоток успішності
            }).reset_index()

            # Видаляємо викиди (суми більше 99-го перцентиля)
            amount_99th = np.percentile(customer_stats['total_amount'], 99)
            customer_stats = customer_stats[customer_stats['total_amount'] <= amount_99th]

            # Створюємо власні межі для груп
            amount_bins = [
                0,  # мінімум
                100,  # до 100 грн
                500,  # до 500 грн
                1000,  # до 1000 грн
                2000,  # до 2000 грн
                5000,  # до 5000 грн
                10000,  # до 10000 грн
                20000,  # до 20000 грн
                float('inf')  # решта
            ]

            # Створюємо мітки для груп
            labels = [
                '0-100',
                '100-500',
                '500-1K',
                '1K-2K',
                '2K-5K',
                '5K-10K',
                '10K-20K',
                '20K+'
            ]

            # Застосовуємо групування
            customer_stats['amount_group'] = pd.cut(
                customer_stats['total_amount'],
                bins=amount_bins,
                labels=labels,
                include_lowest=True
            )

            # Рахуємо статистику для кожної групи
            group_stats = customer_stats.groupby('amount_group').agg({
                'customer_id': 'count',  # кількість клієнтів
                'state': 'mean',  # середній відсоток успішності
                'total_amount': 'mean'  # середня сума замовлення
            }).reset_index()

            # Створення графіку з двома осями
            x = np.arange(len(group_stats))

            # Основні стовпці - середня сума замовлення
            bars = ax.bar(x, group_stats['total_amount'], color='#1f77b4', alpha=0.7)
            ax.set_xlabel('Середня сума замовлення, грн')
            ax.set_ylabel('Середня сума замовлення, грн', color='#1f77b4')
            ax.tick_params(axis='y', labelcolor='#1f77b4')

            # Додаємо другу вісь для успішності
            ax2 = ax.twinx()
            success_line = ax2.plot(x, group_stats['state'], 'o-',
                                    color='gold', linewidth=2, markersize=8)
            ax2.set_ylabel('Середній відсоток успішності (%)', color='gold')
            ax2.tick_params(axis='y', labelcolor='gold')
            ax2.set_ylim(0, 100)

            # Налаштовуємо мітки осі X
            ax.set_xticks(x)
            ax.set_xticklabels(group_stats['amount_group'], rotation=45)

            # Додаємо підписи значень
            for i, (amount, customers) in enumerate(zip(group_stats['total_amount'],
                                                        group_stats['customer_id'])):
                # Підпис середньої суми
                if amount >= 1000:
                    amount_text = f'~{amount / 1000:.0f}K'
                else:
                    amount_text = f'~{amount:.0f}'
                ax.text(i, amount, amount_text,
                        ha='center', va='bottom', color='#1f77b4')
                # Підпис кількості клієнтів
                ax.text(i, 0, f'n={customers}',
                        ha='center', va='top', color='gray')

            # Додаємо підписи успішності
            for i, success in enumerate(group_stats['state']):
                ax2.text(i, success + 2, f'{success:.1f}%',
                         ha='center', va='bottom', color='black')

            # Додаємо легенду
            custom_lines = [bars.patches[0], Line2D([0], [0], color='gold', marker='o', linewidth=2, markersize=8)]
            ax.legend(custom_lines, ['Середня сума замовлення', 'Середній % успішності'], loc='upper left')

            plt.title('Залежність успішності від середньої суми замовлення клієнта')
            plt.tight_layout()

            # Зберігаємо графік
            print("\n8. Saving plot")
            # Зберігаємо графік
            print("\n8. Saving plot")
            image_data = self.save_plot_to_binary(fig, 'customer_amount_success_distribution.png')[0]  # беремо перший елемент кортежу
            print("Image data type:", type(image_data))
            print("Image data size:", len(image_data) if image_data else "None")
            print("Image data type:", type(image_data))
            print("Image data size:", len(image_data) if image_data else "None")

            print("\n9. Closing figure")
            plt.close(fig)

            print("\n10. Returning data")
            return image_data

        except Exception as e:
            print("\n=== Error occurred ===")
            print("Error type:", type(e))
            print("Error message:", str(e))
            import traceback
            print("\nFull traceback:")
            print(traceback.format_exc())
            plt.close('all')
            raise

    def create_customer_amount_success_distribution_plot(self):
        """Analysis of success rate distribution by average order amount"""
        # Отримання даних

        print("\n=== STARTING DATA PROCESSING ===")

        data = self._read_csv_extended_data()
        df = pd.DataFrame(data)
        print(f"DF: {df}")

        # Перевірка на коректність даних у колонці processing_time_hours
        df['processing_time_hours'] = pd.to_numeric(df['processing_time_hours'], errors='coerce')

        # Виведення некоректних даних
        invalid_data = df[df['processing_time_hours'].isna()]
        if not invalid_data.empty:
            print("Некоректні дані в колонці 'processing_time_hours':")
            print(invalid_data[['order_id', 'processing_time_hours']].to_string(index=False))

        # Перевірка та конвертація даних у колонці discount_total
        df['discount_total'] = pd.to_numeric(df['discount_total'], errors='coerce')

        # Виведення некоректних даних
        invalid_data = df[df['discount_total'].isna()]
        if not invalid_data.empty:
            print("Некоректні дані в колонці 'discount_total':")
            print(invalid_data[['order_id', 'discount_total']].to_string(index=False))

        # Заміна некоректних значень на 0
        df['discount_total'] = df['discount_total'].fillna(0)

        # Збереження базової статистики
        self.total_orders = len(df)
        df['is_successful'] = df['state'].apply(lambda x: 1 if x == 'sale' else 0)
        self.success_rate = (df['is_successful'].mean() * 100)
        df['create_date'] = pd.to_datetime(df['create_date'])
        df['date_order'] = pd.to_datetime(df['date_order'])
        df['avg_response_time_days'] = abs((df['date_order'] - df['create_date']).dt.total_seconds() / (3600 * 24))
        self.avg_response_time = df['avg_response_time_days'].mean()
        self.avg_processing_time = df['processing_time_hours'].mean()

        print("\n=== STARTING PLOT CREATION ===")
        # Додаємо діагностичний друк
        print("Available columns:", df.columns.tolist())

        # Закриваємо всі відкриті фігури перед створенням нової
        plt.close('all')

        fig, ax = plt.subplots(figsize=(15, 8))

        # Конвертуємо суму в числовий формат
        df['total_amount'] = pd.to_numeric(df['total_amount'], errors='coerce').fillna(0)

        # Розраховуємо середню суму замовлень для кожного клієнта
        customer_stats = df.groupby('customer_id').agg({
            'total_amount': 'mean',
            'state': lambda x: (x == 'sale').mean() * 100  # відсоток успішності
        }).reset_index()

        # Створюємо 10 груп з приблизно однаковою кількістю клієнтів
        customer_stats['amount_group'] = pd.qcut(customer_stats['total_amount'],
                                                 q=20,
                                                 duplicates='drop')

        # Форматуємо мітки груп
        def format_amount(interval):
            left = int(interval.left)
            right = int(interval.right)

            def format_number(num):
                if num >= 1000000:
                    return f"{num / 1000000:.1f}M"
                elif num >= 1000:
                    return f"{num / 1000:.0f}K"
                return str(int(num))

            return f'{format_number(left)}-{format_number(right)}'

        # Отримуємо межі інтервалів та створюємо нові лейбли
        intervals = customer_stats['amount_group'].cat.categories
        labels = [format_amount(interval) for interval in intervals]

        # Застосовуємо нові лейбли
        customer_stats['amount_group'] = pd.qcut(customer_stats['total_amount'],
                                                 q=20,
                                                 labels=labels,
                                                 duplicates='drop')

        # Рахуємо статистику для кожної групи
        group_stats = customer_stats.groupby('amount_group').agg({
            'customer_id': 'count',  # кількість клієнтів
            'state': 'mean',  # середній відсоток успішності
            'total_amount': 'mean'  # середня сума замовлення
        }).reset_index()

        # Створення графіку з двома осями
        x = np.arange(len(group_stats))

        # Основні стовпці - середня сума замовлення
        bars = ax.bar(x, group_stats['total_amount'], color='#1f77b4', alpha=0.7)
        ax.set_xlabel('Середня сума замовлення, грн')
        ax.set_ylabel('Середня сума замовлення, грн', color='#1f77b4')
        ax.tick_params(axis='y', labelcolor='#1f77b4')

        # Додаємо другу вісь для успішності
        ax2 = ax.twinx()
        success_line = ax2.plot(x, group_stats['state'], 'o-',
                                color='gold', linewidth=2, markersize=8)
        ax2.set_ylabel('Середній відсоток успішності (%)', color='gold')
        ax2.tick_params(axis='y', labelcolor='gold')
        ax2.set_ylim(0, 100)

        # Налаштовуємо мітки осі X
        ax.set_xticks(x)
        ax.set_xticklabels(group_stats['amount_group'], rotation=45)

        # Додаємо підписи значень
        for i, (amount, customers) in enumerate(zip(group_stats['total_amount'],
                                                    group_stats['customer_id'])):
            # Підпис середньої суми
            ax.text(i, amount, f'~{amount / 1000:.0f}K',
                    ha='center', va='bottom', color='#1f77b4')
            # Підпис кількості клієнтів
            ax.text(i, 0, f'n={customers}',
                    ha='center', va='top', color='gray')

        # Додаємо підписи успішності
        for i, success in enumerate(group_stats['state']):
            ax2.text(i, success + 2, f'{success:.1f}%',
                     ha='center', va='bottom', color='black')

        # Додаємо легенду
        custom_lines = [bars.patches[0], Line2D([0], [0], color='gold', marker='o', linewidth=2, markersize=8)]
        ax.legend(custom_lines, ['Середня сума замовлення', 'Середній % успішності'], loc='upper left')

        plt.title('Залежність успішності від середньої суми замовлення клієнта')
        plt.tight_layout()

        buffer = BytesIO()
        print("\n=== Saving plot to buffer ===")
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        print(f"Buffer position after save: {buffer.tell()}")
        buffer.seek(0)
        print(f"Buffer position after seek: {buffer.tell()}")

        binary_data = buffer.getvalue()
        print(f"\n=== Binary data ===")
        print(f"Binary data type: {type(binary_data)}")
        print(f"Binary data length: {len(binary_data)}")

        result = base64.b64encode(binary_data)
        print(f"\n=== Base64 result ===")
        print(f"Result type: {type(result)}")
        print(f"Result length: {len(result)}")

        self.customer_amount_success_distribution_plot = result
        print(f"\n=== Field value ===")
        print(f"Field value type: {type(self.customer_amount_success_distribution_plot)}")
        print(f"Field value length: {len(self.customer_amount_success_distribution_plot)}")
