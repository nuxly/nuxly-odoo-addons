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
        const options = {
            ...this.cachedFilterOptions,
            ledger_navigation_visible_account_ids: this.getVisibleRecordIds("account.account"),
            ledger_navigation_visible_partner_ids: this.getVisibleRecordIds("res.partner"),
        };
        const action = await this.orm.call(
            "account.report",
            "dispatch_report_action",
            [this.cachedFilterOptions.report_id, options, button.action, button.action_param],
            { context: this.action.context }
        );
        return this.actionService.doAction(action, { stackPosition: "replaceCurrentAction" });
    },

    // Records (accounts, partners) of the lines currently shown on screen.
    // The search bar is only applied on the client side, to every loaded line
    // (journal items included): a line is shown when it matches, or when one
    // of its parent or child lines does (see isHiddenBySearchFilter() in
    // line.js). The server cannot know this list, so it is sent along with
    // the button call.
    getVisibleRecordIds(model) {
        const pattern = new RegExp(`~${model.replace(".", "\\.")}~(\\d+)$`);
        const recordIds = [];
        for (const line of this.lines || []) {
            const match = line.id.match(pattern);
            if (!match) {
                continue;
            }
            const isShown =
                !this.lines_searched ||
                this.lines_searched.some(
                    (searchedLineId) =>
                        searchedLineId === line.id || this.isLineRelatedTo(searchedLineId, line.id)
                );
            if (isShown) {
                recordIds.push(parseInt(match[1]));
            }
        }
        return recordIds;
    },
});
