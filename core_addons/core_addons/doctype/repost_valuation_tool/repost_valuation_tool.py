# Copyright (c) 2025, nurholis and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
from frappe.model.document import Document


class RepostValuationTool(Document):
	def on_submit(self):
		self.make_repost_valuation()
	
	def make_repost_valuation(self):
		all_items = frappe.get_all("Item",{"disabled": 0,"is_stock_item": 1},pluck="name")
		all_warehouse = frappe.get_all("Warehouse",{"is_group":0,"disabled": 0},pluck="name")
		total_repost = 0
		for warehouse in all_warehouse:
			for item in all_items:
				doc = frappe.get_doc({
					"doctype":"Repost Item Valuation",
					"based_on":"Item and Warehouse",
					"item_code":item,
					"warehouse":warehouse,
					"posting_date":self.posting_date,
					"posting_time":self.posting_time,
					"allow_negative_stock":1,
					"custom_valuation_tool_reference": self.name
				})
				doc.insert()
				doc.submit()

				total_repost = total_repost + 1
		
		self.total_repost = total_repost
	
def check_and_update_status(repost_done,total_repost,name):
	if flt(repost_done / total_repost) == 1:
		frappe.db.set_value("Repost Valuation Tool",name,"status","Completed")