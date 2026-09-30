from odoo import http
from odoo.http import request

class DashboardController(http.Controller):

    @http.route('/dashboard/filter-apply', type='json', auth='user')
    def filter_apply(self, data):
        startDate = data.get('startDate')
        endDate = data.get('endDate')
        print(startDate)
        print(endDate)
        result = request.env['account.move'].get_data(startDate, endDate)
        return result
