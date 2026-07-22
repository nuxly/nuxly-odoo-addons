/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { formatMonetary } from "@web/views/fields/formatters";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class CumulativeBalanceField extends Component {
    static template = "web_list_cumulative_balance.CumulativeBalanceField";
    static props = { ...standardFieldProps };

    // Formula (S = cumulative balance, N = "balance" of the current row):
    //   - No row selected at all  -> S(1) = N(1), then S(row) = S(previous row) + N(row)
    //   - At least one row selected -> for a SELECTED row: S(row) = S(previous row) + N(row)
    //                                   for an UNSELECTED row: S(row) = S(previous row) (just repeats it)
    // "previous row" always means the row just above on screen, in the current
    // sort/filter order - never the underlying database order.
    //
    // Reading `row.selected` on every row here (not just the current one) makes
    // Owl re-render this cell whenever ANY row is (de)selected, the same
    // reactivity the native list footer total relies on - see computeAggregates()
    // in Odoo's web/static/src/views/list/list_renderer.js.
    get value() {
        const rows = this.props.record.model.root.records;
        const hasSelection = rows.some((row) => row.selected);
        let cumulativeBalance = 0;
        for (const row of rows) {
            if (!hasSelection || row.selected) {
                cumulativeBalance += row.data.balance;
            }
            if (row.id === this.props.record.id) {
                break;
            }
        }
        return cumulativeBalance;
    }

    get formattedValue() {
        return formatMonetary(this.value, {
            data: this.props.record.data,
            currencyField: "company_currency_id",
        });
    }
}

export const cumulativeBalanceField = {
    component: CumulativeBalanceField,
    supportedTypes: ["monetary"],
};

registry.category("fields").add("cumulative_balance", cumulativeBalanceField);
