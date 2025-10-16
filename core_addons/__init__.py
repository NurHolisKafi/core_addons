__version__ = "0.0.1"
import frappe
from erpnext.stock.doctype.repost_item_valuation import repost_item_valuation
from erpnext.stock.doctype.repost_item_valuation.repost_item_valuation import repost_sl_entries,repost_gl_entries,remove_attached_file,notify_error_to_stock_managers,RecoverableErrors

def custom_repost(doc):
    try:
        frappe.flags.through_repost_item_valuation = True
        if not frappe.db.exists("Repost Item Valuation", doc.name):
            return

        # This is to avoid TooManyWritesError in case of large reposts
        frappe.db.MAX_WRITES_PER_TRANSACTION *= 4

        doc.set_status("In Progress")
        if not frappe.flags.in_test:
            frappe.db.commit()

        if doc.recreate_stock_ledgers:
            doc.recreate_stock_ledger_entries()

        repost_sl_entries(doc)
        repost_gl_entries(doc)

        doc.set_status("Completed")
        # tambahan
        update_data_repost_tool(doc)
        # 
        doc.db_set("reposting_data_file", None)
        remove_attached_file(doc.name)

    except Exception as e:
        if frappe.flags.in_test:
            # Don't silently fail in tests,
            # there is no reason for reposts to fail in CI
            raise

        frappe.db.rollback()
        traceback = frappe.get_traceback(with_context=True)
        doc.log_error("Unable to repost item valuation")

        message = frappe.message_log.pop() if frappe.message_log else ""
        if isinstance(message, dict):
            message = message.get("message")

        status = "Failed"
        # If failed because of timeout, set status to In Progress
        if traceback and ("timeout" in traceback.lower() or "Deadlock found" in traceback):
            status = "In Progress"

        if traceback:
            message += "<br><br>" + "<b>Traceback:</b> <br>" + traceback

        frappe.db.set_value(
            doc.doctype,
            doc.name,
            {
                "error_log": message,
                "status": status,
            },
        )

        if status == "Failed":
            outgoing_email_account = frappe.get_cached_value(
                "Email Account", {"default_outgoing": 1, "enable_outgoing": 1}, "name"
            )

            if outgoing_email_account and not isinstance(e, RecoverableErrors):
                notify_error_to_stock_managers(doc, message)
                doc.set_status("Failed")
    finally:
        if not frappe.flags.in_test:
            frappe.db.commit()


def update_data_repost_tool(self):
    from core_addons.core_addons.doctype.repost_valuation_tool.repost_valuation_tool import check_and_update_status
    tool_name = self.custom_valuation_tool_reference
    if tool_name:
        curr_repost_done, total_repost = frappe.get_value("Repost Valuation Tool",tool_name,["repost_done","total_repost"]) or 0
        repost_done = curr_repost_done + 1
        frappe.db.set_value("Repost Valuation Tool",tool_name,"repost_done",repost_done)
        check_and_update_status(repost_done,total_repost,tool_name)


repost_item_valuation.repost = custom_repost