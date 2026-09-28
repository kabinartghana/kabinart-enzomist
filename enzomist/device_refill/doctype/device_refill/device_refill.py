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

        # Work out the quantity in a unit the item understands.
        # Oil is refilled in mL; the item may be stocked in Nos (bottles), Litre or mL.
        item = frappe.get_doc("Item", placement.scent_oil_item)
        ml_uom = next((u for u in item.uoms if u.uom in ("Millilitre", "ml", "mL")), None)
        if item.stock_uom in ("Millilitre", "ml", "mL"):
            uom, qty = item.stock_uom, self.amount_refilled_ml
        elif ml_uom:
            uom, qty = ml_uom.uom, self.amount_refilled_ml
        elif item.stock_uom == "Litre":
            uom, qty = "Litre", self.amount_refilled_ml / 1000
        else:
            # Refill is still recorded; stock is simply not deducted until the item has a mL conversion.
            frappe.msgprint(
                f"Refill saved, but stock was NOT deducted: item {item.name} is stocked in {item.stock_uom}. "
                f"Add a 'Millilitre' row to its UOM Conversion table (e.g. 1 Millilitre = 1/150 Nos for a 150 mL bottle).",
                indicator="orange", alert=True
            )
            return

        # Material Issue: takes the oil out of the Enzomist warehouse
        se = frappe.new_doc("Stock Entry")
        se.stock_entry_type = "Material Issue"
        se.purpose = "Material Issue"
        se.remarks = f"Refill: {self.name} | Placement: {self.placement} | QB Ref: {self.qb_estimate_no or 'N/A'}"

        se.append("items", {
            "item_code": placement.scent_oil_item,
            "qty": qty,
            "uom": uom,
            "s_warehouse": warehouse,
        })

        # If stock can't be deducted (e.g. not enough oil in stock), keep the refill
        # and tell the user, rather than blocking the refill record.
        frappe.db.savepoint("enzomist_refill_stock")
        try:
            se.insert(ignore_permissions=True)
            se.submit()
        except Exception as e:
            frappe.db.rollback(save_point="enzomist_refill_stock")
            frappe.clear_messages()
            frappe.log_error(title=f"Enzomist refill {self.name}: stock not deducted")
            frappe.msgprint(
                f"Refill saved, but stock was NOT deducted: {frappe.utils.strip_html(str(e))}",
                indicator="orange", alert=True
            )
            return

        frappe.msgprint(
            f"Stock Entry {se.name} created — {self.amount_refilled_ml}mL deducted from {placement.scent_oil_item}",
            alert=True
        )
