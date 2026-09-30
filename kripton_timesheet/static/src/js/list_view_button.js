odoo.define('kripton_timesheet.list_view_button', function (require) {
    "use strict";
    var ListController = require('web.ListController');
    var ListView = require('web.ListView');
    var viewRegistry = require('web.view_registry');
  var TreeButton = ListController.extend({
   buttons_template: 'kripton_timesheet.buttons',
   events: _.extend({}, ListController.prototype.events, {
       'click .open_wizard_action': '_OpenWizard',
   }),
   _OpenWizard: function () {
       var self = this;
        this.do_action({
           type: 'ir.actions.act_window',
           res_model: 'account.analytic.line.wizard',
           name :'My Timesheets',
           view_mode: 'form',
           view_type: 'form',
           views: [[false, 'form']],
           target: 'new',
           res_id: false,
       });
   }
});
    var SaleOrderListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: TreeButton,
        }),
    });
    viewRegistry.add('saleorder_btn_tree', SaleOrderListView);
});