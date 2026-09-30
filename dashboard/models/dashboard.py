from collections import defaultdict
from odoo import models, fields, api
from datetime import datetime, timedelta
class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def get_data(self, startDate=None, endDate=None):

        print("startDate", startDate)
        print("endDate", endDate)

        # Convert startDate and endDate to datetime.date if they are in string format
        if isinstance(startDate, str):
            startDate = datetime.strptime(startDate, '%Y-%m-%d').date()  # Convert string to date
        elif isinstance(startDate, datetime):
            startDate = startDate.date()  # Convert datetime to date
        if isinstance(endDate, str):
            endDate = datetime.strptime(endDate, '%Y-%m-%d').date()  # Convert string to date
        elif isinstance(endDate, datetime):
            endDate = endDate.date()


        # Gather cost data
        cost_data = self.env['cost.employee'].search([])
        grouped_data = defaultdict(lambda: {'costs': 0})
        grouped_data_quarter = defaultdict(lambda: {'costs': 0})
        grouped_data_year = defaultdict(lambda: {'costs': 0})

        for cost in cost_data:
            if cost.date and  startDate <= cost.date <= endDate:
                month = cost.date.strftime('%Y-%m')
                year = cost.date.strftime('%Y')
                quarter = f'{year}-Q{((cost.date.month - 1) // 3) + 1}'
                grouped_data[month]['costs'] += cost.cost
                grouped_data_quarter[quarter]['costs'] += cost.cost
                grouped_data_year[year]['costs'] += cost.cost

        # Gather sales invoices data
        invoices = self.search([('move_type', '=', 'out_invoice')])
        grouped_data_sales = defaultdict(lambda: {'amount_net': 0, 'amount_untaxed': 0})
        grouped_data_sales_quarter = defaultdict(lambda: {'amount_net': 0, 'amount_untaxed': 0})
        grouped_data_sales_year = defaultdict(lambda: {'amount_net': 0, 'amount_untaxed': 0})

        for invoice in invoices:
            if invoice.ausgangsrechnungen_date and  startDate <= invoice.ausgangsrechnungen_date <= endDate:  # Check if the invoice date exists
                month = invoice.ausgangsrechnungen_date.strftime('%Y-%m')
                year = invoice.ausgangsrechnungen_date.strftime('%Y')
                quarter = f'{year}-Q{((invoice.ausgangsrechnungen_date.month - 1) // 3) + 1}'

                grouped_data_sales[month]['amount_net'] += invoice.amount_untaxed_signed
                grouped_data_sales[month]['amount_untaxed'] += invoice.amount_untaxed

                grouped_data_sales_quarter[quarter]['amount_net'] += invoice.amount_untaxed_signed
                grouped_data_sales_quarter[quarter]['amount_untaxed'] += invoice.amount_untaxed

                grouped_data_sales_year[year]['amount_net'] += invoice.amount_untaxed_signed
                grouped_data_sales_year[year]['amount_untaxed'] += invoice.amount_untaxed

        # Gather purchase invoice data
        bills = self.search([('move_type', '=', 'in_invoice')])
        grouped_data_purchases = defaultdict(lambda: {'amount_net': 0, 'amount_untaxed': 0})
        grouped_data_purchases_quarter = defaultdict(lambda: {'amount_net': 0, 'amount_untaxed': 0})
        grouped_data_purchases_year = defaultdict(lambda: {'amount_net': 0, 'amount_untaxed': 0})

        for bill in bills:
            if bill.end_date_timesheets and  startDate <= bill.end_date_timesheets <= endDate: # Check if the bill date exists
                month = bill.end_date_timesheets.strftime('%Y-%m')
                year = bill.end_date_timesheets.strftime('%Y')
                quarter = f'{year}-Q{((bill.end_date_timesheets.month - 1) // 3) + 1}'

                grouped_data_purchases[month]['amount_net'] += bill.amount_untaxed_signed
                grouped_data_purchases[month]['amount_untaxed'] += bill.amount_untaxed

                grouped_data_purchases_quarter[quarter]['amount_net'] += bill.amount_untaxed_signed
                grouped_data_purchases_quarter[quarter]['amount_untaxed'] += bill.amount_untaxed

                grouped_data_purchases_year[year]['amount_net'] += bill.amount_untaxed_signed
                grouped_data_purchases_year[year]['amount_untaxed'] += bill.amount_untaxed
        all_months = sorted(
            set(grouped_data.keys()) | set(grouped_data_sales.keys()) | set(grouped_data_purchases.keys()),
            key=lambda x: (int(x.split('-')[1]), int(x.split('-')[0]))  # Trier par mois, puis par année
        )

        all_quarters = sorted(
            set(grouped_data_quarter.keys()) | set(grouped_data_sales_quarter.keys()) | set(
                grouped_data_purchases_quarter.keys()),
            key=lambda x: (int(x.split('-')[1][1]), int(x.split('-')[0]))  # Trier par trimestre, puis par année
        )

        all_years = sorted(
            set(grouped_data_year.keys()) | set(grouped_data_sales_year.keys()) | set(
                grouped_data_purchases_year.keys())
        )
        print("all_months", all_months)
        print("all_quarters", all_quarters)
        print("all_years", all_years)

        # Prepare the result
        result = {
            'month_sales': [],
            'quarter_sales': [],
            'year_sales': [],
            'month_amount_net_sales': [],
            'quarter_amount_net_sales': [],
            'year_amount_net_sales': [],
            'month_amount_untaxed_sales': [],
            'year_amount_untaxed_sales': [],
            'quarter_amount_untaxed_sales': [],
            'month_purchases': [],
            'year_purchases': [],
            'quarter_purchases': [],
            'month_amount_net_purchases': [],
            'year_amount_net_purchases': [],
            'quarter_amount_net_purchases': [],
            'month_amount_untaxed_purchases': [],
            'year_amount_untaxed_purchases': [],
            'quarter_amount_untaxed_purchases': [],
            'dates_month': all_months,
            'dates_quarter': all_quarters,
            'dates_year': all_years,
            'costs_month': [],
            'costs_quarter': [],
            'costs_year': [],
            'cost_totel_month': [],
            'cost_totel_quarter': [],
            'cost_totel_year': [],
            'marge_net_month': [],
            'marge_net_year': [],
            'marge_net_quarter': []
        }

        for month in all_months:
            total_sales = grouped_data_sales[month]['amount_net']
            total_untaxed_sales = grouped_data_sales[month]['amount_untaxed']
            result['month_sales'].append(month)
            result['month_amount_net_sales'].append(total_sales)
            result['month_amount_untaxed_sales'].append(total_untaxed_sales)

            total_purchases = grouped_data_purchases[month]['amount_net']
            total_untaxed_purchases = grouped_data_purchases[month]['amount_untaxed']
            result['month_purchases'].append(month)
            result['month_amount_net_purchases'].append(total_purchases)
            result['month_amount_untaxed_purchases'].append(total_untaxed_purchases)

            total_costs = grouped_data[month]['costs']
            result['costs_month'].append(total_costs)

            cost_total_value = total_costs - total_purchases
            result['cost_totel_month'].append(cost_total_value)

            # Margin calculation
            margin_net_value = total_sales - (-total_purchases + total_costs)
            result['marge_net_month'].append(margin_net_value)

        for quarter in all_quarters:
            total_sales = grouped_data_sales_quarter[quarter]['amount_net']
            total_untaxed_sales = grouped_data_sales_quarter[quarter]['amount_untaxed']
            result['quarter_sales'].append(quarter)
            result['quarter_amount_net_sales'].append(total_sales)
            result['quarter_amount_untaxed_sales'].append(total_untaxed_sales)

            total_purchases = grouped_data_purchases_quarter[quarter]['amount_net']
            total_untaxed_purchases = grouped_data_purchases_quarter[quarter]['amount_untaxed']
            result['quarter_purchases'].append(quarter)
            result['quarter_amount_net_purchases'].append(total_purchases)
            result['quarter_amount_untaxed_purchases'].append(total_untaxed_purchases)

            total_costs = grouped_data_quarter[quarter]['costs']
            result['costs_quarter'].append(total_costs)

            cost_total_value = total_costs - total_purchases
            result['cost_totel_quarter'].append(cost_total_value)

            # Margin calculation
            margin_net_value = total_sales - (-total_purchases + total_costs)
            result['marge_net_quarter'].append(margin_net_value)

        for year in all_years:
            total_sales = grouped_data_sales_year[year]['amount_net']

            total_untaxed_sales = grouped_data_sales_year[year]['amount_untaxed']

            result['year_sales'].append(year)
            result['year_amount_net_sales'].append(total_sales)
            result['year_amount_untaxed_sales'].append(total_untaxed_sales)

            total_purchases = grouped_data_purchases_year[year]['amount_net']
            total_untaxed_purchases = grouped_data_purchases_year[year]['amount_untaxed']
            result['year_purchases'].append(year)
            result['year_amount_net_purchases'].append(total_purchases)
            result['year_amount_untaxed_purchases'].append(total_untaxed_purchases)

            total_costs = grouped_data_year[year]['costs']
            result['costs_year'].append(total_costs)

            cost_total_value = total_costs - total_purchases
            result['cost_totel_year'].append(cost_total_value)

            # Margin calculation
            margin_net_value = total_sales - (-total_purchases + total_costs)
            result['marge_net_year'].append(margin_net_value)
            print('result',result)

        return result

