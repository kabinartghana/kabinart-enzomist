import frappe
from frappe.model.document import Document

class DeviceRefill(Document):
    def on_submit(self):
        """On submit:
        1. Update linked Placement last_refill_date
        2. Recalculate predicted refill date
        3. Create Stock Entry deducting mL from bulk oil jug
        """
        self.update_placement()
        self.create_stock_entry()

    def update_placement(self):
        placement = frappe.get_doc("Device Placement", self.placement)
        placement.last_refill_date = self.date_refilled
        placement.calculate_predicted_refill_date()
        placement.save(ignore_permissions=True)

    def create_stock_entry(self):
        placement = frappe.get_doc("Device Placement", self.placement)

        if not placement.scent_oil_item:
            frappe.throw("Placement has no scent/oil item set — cannot deduct stock.")

        # Get Enzomist warehouse
        warehouse = frappe.db.get_value(
            "Warehouse",
            {"warehouse_name": ["like", "%Enzomist%"], "is_group": 0},
            "name"
        )
        if not warehouse:
            frappe.throw("Enzomist Main Warehouse not found. Please create it in Stock > Warehouses.")

        # Create material consumption Stock Entry
        se = frappe.new_doc("Stock Entry")
        se.stock_entry_type = "Material Consumption for Manufacture"
        se.purpose = "Material Consumption for Manufacture"
        se.remarks = f"Refill: {self.name} | Placement: {self.placement} | QB Ref: {self.qb_estimate_no or 'N/A'}"

        se.append("items", {
            "item_code": placement.scent_oil_item,
            "qty": self.amount_refilled_ml / 1000,  # convert mL to L if UOM is litres
            "uom": "mL",
            "s_warehouse": warehouse,
        })

        se.insert(ignore_permissions=True)
        se.submit()

        frappe.msgprint(
            f"Stock Entry {se.name} created — {self.amount_refilled_ml}mL deducted from {placement.scent_oil_item}",
            alert=True
        )
