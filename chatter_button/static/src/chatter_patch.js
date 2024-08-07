/* @odoo-module */

import { Chatter } from "@mail/core/web/chatter";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { useAttachmentUploader } from "@mail/core/common/attachment_uploader_hook";

patch(Chatter.prototype, {
   async showInfo() {
       const threadId = parseInt(this.props.threadId, 10);
       const threadModel = this.props.threadModel;
       console.log(this);

       await this.env.services.action.doAction({
           type: "ir.actions.client",
           name: _t("Instance information"),
           tag: 'display_notification',
           params: {
                        title: _t("Instance information"),
                        message: `${threadModel} (${threadId})`,
                        sticky: false,
           }
       });
   },
});
