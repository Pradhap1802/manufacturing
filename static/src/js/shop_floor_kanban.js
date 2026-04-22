/** @odoo-module **/

if (window.matchMedia('(display-mode: standalone)').matches) {
    document.documentElement.classList.add('o_scoped_app');
    document.addEventListener("DOMContentLoaded", () => {
        document.body.classList.add('o_scoped_app');
    });
}

import { KanbanController } from "@web/views/kanban/kanban_controller";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class ShopFloorKanbanController extends KanbanController {
    setup() {
        super.setup(...arguments);
        this.actionService = useService("action");
        this.pwa = useService("pwa");
    }

    get canInstallShopFloor() {
        // Only show install button if PWA is supported and NOT already installed
        return this.pwa.isAvailable && !this.pwa.isInstalled;
    }

    exitShopFloor() {
        this.actionService.doAction("mrp.mrp_production_action", { clearBreadcrumbs: true });
    }
}

ShopFloorKanbanController.template = "manufacturing.ShopFloorKanbanView";

registry.category("views").add("mrp_shop_floor_kanban", {
    ...kanbanView,
    Controller: ShopFloorKanbanController,
});
