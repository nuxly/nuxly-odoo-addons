/** @odoo-module **/

import { AccountReportController } from "@account_reports/components/account_report/controller";
import { AccountReportLineName } from "@account_reports/components/account_report/line_name/line_name";
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
                { ...this.cachedFilterOptions, ...this.getLedgerNavigationScreenList() },
                button.action,
                button.action_param,
            ],
            { context: this.action.context }
        );
        return this.actionService.doAction(action, { stackPosition: "replaceCurrentAction" });
    },

    // The accounts shown on screen by the search bar. The search is only
    // applied on the client side, to every loaded line (journal items
    // included): a line is shown when it matches, or when one of its parent
    // or child lines does (see isHiddenBySearchFilter() in line.js). The
    // server cannot know this list, so it is sent along with the call:
    // - the account lines shown,
    // - the account group lines matching the search, whose accounts are all
    //   shown, including the ones of a folded group, not loaded yet.
    // Both are null without any search on screen: Odoo may still keep a
    // search text in the options, restored from the browser session while
    // the search bar input is empty, which must not restrict anything.
    getLedgerNavigationScreenList() {
        if (!this.lines_searched) {
            return {
                ledger_navigation_visible_account_ids: null,
                ledger_navigation_matched_group_ids: null,
            };
        }
        const accountIds = [];
        for (const line of this.lines || []) {
            const match = line.id.match(/~account\.account~(\d+)$/);
            const isShown = this.lines_searched.some(
                (searchedLineId) => searchedLineId === line.id || this.isLineRelatedTo(searchedLineId, line.id)
            );
            if (match && isShown) {
                accountIds.push(parseInt(match[1]));
            }
        }
        const groupIds = [];
        for (const searchedLineId of this.lines_searched) {
            const match = searchedLineId.match(/~account\.group~(\d+)$/);
            if (match) {
                groupIds.push(parseInt(match[1]));
            }
        }
        return {
            ledger_navigation_visible_account_ids: accountIds,
            ledger_navigation_matched_group_ids: groupIds,
        };
    },
});

patch(AccountReportLineName.prototype, {
    // "General ledger" option of an account line (trial balance...): the
    // accounts shown on screen are sent too, so that the previous / next
    // buttons of the general ledger only go through them.
    async caretAction(caretOption) {
        if (caretOption.action !== "caret_option_open_general_ledger") {
            return super.caretAction(...arguments);
        }
        const action = await this.orm.call(
            "account.report",
            "dispatch_report_action",
            [
                this.controller.options.report_id,
                { ...this.controller.options, ...this.controller.getLedgerNavigationScreenList() },
                caretOption.action,
                { line_id: this.props.line.id, action_param: caretOption.action_param },
            ],
            { context: this.controller.context }
        );
        return this.action.doAction(action);
    },
});
