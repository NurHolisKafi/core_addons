import frappe
from core_addons.core_addons.doctype.repost_valuation_tool.repost_valuation_tool import check_and_update_status

def update_repost_tool(self,method):
    old_doc = self.get_doc_before_save()
    if self.status == "Completed" and old_doc.status != "Completed":
        tool_name = self.custom_valuation_tool_reference
        if tool_name:
            curr_repost_done, total_repost = frappe.get_value("Repost Valuation Tool",tool_name,["repost_done","total_repost"]) or 0
            repost_done = curr_repost_done + 1
            frappe.db.set_value("Repost Valuation Tool",tool_name,"repost_done",repost_done)
            check_and_update_status(repost_done,total_repost,tool_name)