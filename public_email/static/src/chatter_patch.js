/* @odoo-module */

import { Chatter } from "@mail/core/web/chatter";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { useAttachmentUploader } from "@mail/core/common/attachment_uploader_hook";

patch(Chatter.prototype, {
   async publicEmail() {
       const threadId = parseInt(this.props.threadId, 10);
       const form = await this.orm.searchRead(
            "ir.ui.view",
            [
                ["name", "=", "mail.compose.message.public.form"],
                ["model", "=", "mail.compose.message"],
            ],
            ["id"]
       );
       const formId = form[0].id;

       await this.env.services.action.doAction({
           type: "ir.actions.act_window",
           name: _t("Send Public Email"),
           res_model: "mail.compose.message",
           view_mode: "form",
           view_type: "form",
           views: [[formId, 'form']],
           target: 'new',
           context: {
               default_composition_mode: 'mass_mail',
               default_model: this.props.threadModel,
               default_res_ids: [threadId],
               default_subject: _t("Public Email"),
               mail_post_autofollow: false,
               default_partner_ids: [],
           },
       });
   },
});
