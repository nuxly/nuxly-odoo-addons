/** @odoo-module **/

import { onMounted, onPatched } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";

const ACCOUNT_MODELS = new Set(["account.move.line"]);
const STICKY_FOOTER_CLASS = "o_account_sticky_footer";

function getResModel(renderer) {
    return (
        renderer.props?.list?.resModel ||
        renderer.props?.list?.model?.root?.resModel ||
        renderer.props?.list?.model?.resModel ||
        renderer.props?.list?.model?.config?.resModel ||
        renderer.env?.searchModel?.resModel ||
        null
    );
}

patch(ListRenderer.prototype, {
    setup() {
        super.setup(...arguments);

        const syncStickyFooter = () => {
            if (!this.el) {
                return;
            }

            const modelFromProps = getResModel(this);
            const modelFromDom = this.el.querySelector(
                "thead [data-tooltip-info*='account.move.line']"
            )
                ? "account.move.line"
                : null;
            const enableStickyFooter = ACCOUNT_MODELS.has(modelFromProps || modelFromDom);
            this.el.classList.toggle(STICKY_FOOTER_CLASS, enableStickyFooter);

            for (const footer of this.el.querySelectorAll(".o_list_footer")) {
                footer.classList.toggle(STICKY_FOOTER_CLASS, enableStickyFooter);
            }
        };

        onMounted(syncStickyFooter);
        onPatched(syncStickyFooter);
    },
});
