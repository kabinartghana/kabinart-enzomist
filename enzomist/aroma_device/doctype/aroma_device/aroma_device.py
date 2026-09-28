import frappe
from frappe.model.document import Document

class AromaDevice(Document):
    def validate(self):
        # Warn if k-value is missing
        if not self.k_value:
            self.data_quality_note = (
                "No consumption data — refill prediction unavailable. "
                "A k-value must be measured before predictions can run for this model."
            )
        # Warn if k-value spread is high (unreliable)
        elif self.k_spread_pct and self.k_spread_pct > 0:
            self.data_quality_note = (
                f"Refill date is an estimate — k-value variance is {self.k_spread_pct}%. "
                "Verify with an actual consumption reading before billing."
            )
        else:
            self.data_quality_note = ""
