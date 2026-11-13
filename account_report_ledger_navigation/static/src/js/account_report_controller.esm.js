/** @odoo-module **/

import { AccountReportController } from "@account_reports/components/account_report/controller";
import { patch } from "@web/core/utils/patch";

patch(AccountReportController.prototype, {
    // The previous / next buttons open the adjacent ledger in place of the
    // current one: going through 50 accounts must not leave 50 breadcrumbs.
    // The native reportAction() always stacks the returned action, hence the
    // server call is done here to pass the stackPosition option.
    async buttonAction(ev, button) {
        if (!button.replace_current_action) {
            return super.buttonAction(...arguments);
        }
        ev?.preventDefault();
        ev?.stopPropagation();
        const action = await this.orm.call(
            "account.report",
            "dispatch_report_action",
            [
                this.cachedFilterOptions.report_id,
                this.cachedFilterOptions,
                button.action,
                button.action_param,
            ],
            { context: this.action.context }
        );
        return this.actionService.doAction(action, { stackPosition: "replaceCurrentAction" });
    },
});
