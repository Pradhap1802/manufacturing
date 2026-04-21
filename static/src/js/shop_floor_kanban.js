/** @odoo-module **/

import { KanbanController } from "@web/views/kanban/kanban_controller";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class ShopFloorKanbanController extends KanbanController {
    setup() {
        super.setup(...arguments);
        this.actionService = useService("action");
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
