/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const customButtonAction = {
    type: "ir.actions.client",
    tag: "custom_button_action",
    name: "Custom Button Action",
    params: {},
    target: "new",
}

function executeCustomAction(env) {
    const notification = env.services.notification;
    console.log("Custom button clicked!");
    notification.add("Success!", {
        type: "success",
        message: "Button clicked successfully!",
        sticky: false,
    });
    return Promise.resolve();
}

registry.category("actions").add("custom_button_action", executeCustomAction);