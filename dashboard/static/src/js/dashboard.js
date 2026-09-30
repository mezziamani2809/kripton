odoo.define('dashboard.CostDashboard', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');

    var CostDashboard = AbstractAction.extend({
        contentTemplate: 'CostDashboard',

        events: {
            'change #period_filter': 'onchange_period',
            'change #year_filter': 'onchange_period',
            'click #apply_filters': 'onApplyFilters'
        },
        charts: {},

        start: function() {
            var self = this;

            // Écouteur pour les cases à cocher d'année
            this.$el.find('input[name="year_filter"]').on('change', function() {
                var selectedYears = self.getSelectedYears();
                console.log("Années sélectionnées:", selectedYears);  // Debugging the selected years

                // Limiter la sélection à un maximum de 3 années
                if (selectedYears && selectedYears.length > 2) {
                    self.$el.find('input[name="year_filter"]:checked:last').prop('checked', false);
                    alert("Vous ne pouvez sélectionner que 3 années maximum.");
                }
            });

            return this._super.apply(this, arguments);
        },

        getSelectedYears: function() {
            var selectedYears = [];
            this.$el.find('label').removeClass('selected-year-red');
            // Collecting the checked years and sorting them based on the order in the DOM
            this.$el.find('input[name="year_filter"]:checked').each(function() {
                selectedYears.push($(this).val());
        $(this).closest('label').addClass('selected-year-red');

            });

            // Sort selected years in ascending order (or you can adjust the sorting logic)
            selectedYears.sort((a, b) => a - b);  // Sort numerically in ascending order
            console.log("Selected years in getSelectedYears (sorted):", selectedYears);
            return selectedYears;
        },

        destroyCharts: function() {
            for (var key in this.charts) {
                if (this.charts[key]) {
                    this.charts[key].destroy();
                }
            }
            this.charts = {};
        },

onApplyFilters: function() {
    var selectedYears = this.getSelectedYears();  // Get selected years
    if (selectedYears.length > 0) {
        var startYear = selectedYears[0];
        // Corrected: January is month 0, December is month 11
        var startDate = new Date(startYear, 0, 1);  // January 1st (month 0)
        // Format the date as 'YYYY-MM-DD'
        var formattedStartDate = startDate.getFullYear() + '-' + (startDate.getMonth() + 1).toString().padStart(2, '0') + '-' + startDate.getDate().toString().padStart(2, '0');

        var endYear = selectedYears[selectedYears.length - 1];
        console.log("endYear:", endYear);

        var endDate = new Date(endYear, 11, 31);  // December 31st (month 11)
        // Format the date as 'YYYY-MM-DD'
        var formattedEndDate = endDate.getFullYear() + '-' + (endDate.getMonth() + 1).toString().padStart(2, '0') + '-' + endDate.getDate().toString().padStart(2, '0');

        console.log("Start Date:", formattedStartDate, "End Date:", formattedEndDate);

        this.applyDateFilter(formattedStartDate, formattedEndDate);
    } else {
        alert("Veuillez sélectionner au moins une année.");
    }
},


        applyDateFilter: function(startDate, endDate) {
            var self = this;

            rpc.query({
                model: 'account.move',
                method: 'get_data',
                args: [startDate, endDate],  // Ensure date is passed in ISO format
            }).then(function(result) {

                var selected_filter = $('#period_filter').val();
                self.destroyCharts();

                if (selected_filter === 'month') {
                    self.renderCharts(result, 'month');
                } else if (selected_filter === 'quarter') {
                    self.renderCharts(result, 'quarter');
                } else {
                    self.renderCharts(result, 'year');
                }
            });
        },

        onchange_period: function(ev) {
            this.onApplyFilters(); // Reapply filters when the period changes
        },

        renderCharts: function(result, period) {

            var last15Months = result[`dates_${period}`].slice(-15);
            var last15Costs = result[`costs_${period}`].slice(-15);
            var last15MonthsSales = result[`${period}_sales`].slice(-15);
            console.log("last15MonthsSales", last15MonthsSales); // Log the entire result

            var last15AmountsNetSales = result[`${period}_amount_net_sales`].slice(-15);
            console.log("last15AmountsNetSales", last15AmountsNetSales); // Log the entire result

            var last15CostTotal = result[`cost_totel_${period}`].slice(-15);
            var last15MonthsPurchases = result[`${period}_purchases`].slice(-15);
            var last15AmountsUntaxedPurchases = result[`${period}_amount_untaxed_purchases`].slice(-15);
            var last15GrossMargin = result[`marge_net_${period}`].slice(-15);

            var ctxSales = document.getElementById('invoice_chart_sales').getContext('2d');
            var ctxCost = document.getElementById('invoice_chart_cost').getContext('2d');
            var ctxCostCa = document.getElementById('invoice_chart_cost_ca').getContext('2d');
            var ctxPurchases = document.getElementById('invoice_chart_purchases').getContext('2d');
            var ctxMarginn = document.getElementById('margin_chart').getContext('2d');
            var ctxEmployeeCost = document.getElementById('cost_chart').getContext('2d');

            // Only render if contexts are available
            if (ctxSales && ctxCost && ctxCostCa && ctxPurchases && ctxMarginn && ctxEmployeeCost) {
                this.createChart(ctxEmployeeCost, 'Employee Cost', last15Months, last15Costs, 'rgba(255, 182, 193, 0.2)', 'rgba(255, 105, 180, 1)');
                this.createChart(ctxCost, 'Cost', last15MonthsSales, last15CostTotal, 'rgba(255, 99, 132, 0.2)', 'rgba(255, 99, 132, 1)');
                this.createChart(ctxSales, 'CA', last15MonthsSales, last15AmountsNetSales, 'rgba(75, 192, 192, 0.2)', 'rgba(75, 192, 192, 1)');
                this.createChart(ctxCostCa, 'CA and Cost', last15MonthsSales, last15AmountsNetSales, 'rgba(75, 192, 192, 0.2)', 'rgba(75, 192, 192, 1)', last15CostTotal, 'rgba(255, 99, 132, 0.2)', 'rgba(255, 99, 132, 1)');
                this.createChart(ctxPurchases, 'Consultants Cost', last15MonthsPurchases, last15AmountsUntaxedPurchases, 'rgba(255, 159, 64, 0.2)', 'rgba(255, 159, 64, 1)');
                this.createChart(ctxMarginn, 'Gross Margin', last15MonthsPurchases, last15GrossMargin, 'rgba(85, 164, 230, 0.2)', 'rgba(85, 164, 230, 1)');
            }
        },

        createChart: function(ctx, label, labels, data, bgColor, borderColor, secondaryData = null, secondaryBgColor = null, secondaryBorderColor = null) {
            var datasets = [{
                label: label,
                data: data,
                backgroundColor: bgColor,
                borderColor: borderColor,
                borderWidth: 1
            }];

            if (secondaryData) {
                datasets.push({
                    label: `${label} (Secondary)`,
                    data: secondaryData,
                    backgroundColor: secondaryBgColor,
                    borderColor: secondaryBorderColor,
                    borderWidth: 1
                });
            }

            this.charts[label] = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: datasets
                },
                options: {
                    scales: {
                        x: { beginAtZero: true },
                        y: { beginAtZero: true }
                    }
                }
            });
        }
    });

    core.action_registry.add('cost_dashboard_tag', CostDashboard);
    return CostDashboard;
});
