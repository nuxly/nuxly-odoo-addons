import { patch } from "@web/core/utils/patch";
import { useChildSubEnv } from "@odoo/owl";
import { CompanySelector, SwitchCompanyMenu } from "@web/webclient/switch_company_menu/switch_company_menu";
import { SwitchCompanyItem } from "@web/webclient/switch_company_menu/switch_company_item";

patch(CompanySelector.prototype, {
    /** @returns {boolean} whether a range was actually selected */
    selectRange(fromCompanyId, toCompanyId, companyIds) {
        const fromIndex = companyIds.indexOf(fromCompanyId);
        const toIndex = companyIds.indexOf(toCompanyId);
        if (fromIndex === -1 || toIndex === -1) {
            return false;
        }
        const [start, end] = fromIndex < toIndex ? [fromIndex, toIndex] : [toIndex, fromIndex];
        for (const companyId of companyIds.slice(start, end + 1)) {
            if (this._isCompanyAllowed(companyId) && !this.selectedCompaniesIds.includes(companyId)) {
                this.selectedCompaniesIds.push(companyId);
            }
        }
        return true;
    },
});

patch(SwitchCompanyMenu.prototype, {
    setup() {
        super.setup();
        useChildSubEnv({
            getVisibleCompanyIds: () => this.visibleCompanies.map((entry) => entry.company.id),
        });
    },
});

patch(SwitchCompanyItem.prototype, {
    toggleCompany(ev) {
        if (!this.isCompanyAllowed) {
            return;
        }
        const companyId = this.props.company.id;
        const didSelectRange =
            ev?.shiftKey &&
            this.companySelector.lastToggledCompanyId &&
            this.companySelector.selectRange(
                this.companySelector.lastToggledCompanyId,
                companyId,
                this.env.getVisibleCompanyIds()
            );
        if (!didSelectRange) {
            super.toggleCompany();
        }
        this.companySelector.lastToggledCompanyId = companyId;
    },
});
