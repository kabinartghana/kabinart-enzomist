import frappe
from frappe.model.document import Document
from frappe.utils import add_days, today
from math import floor

class DevicePlacement(Document):
    def validate(self):
        self.update_data_quality_warning()
        self.calculate_predicted_refill_date()

    def update_data_quality_warning(self):
        if self.device_model:
            device = frappe.get_doc("Aroma Device", self.device_model)
            self.data_quality_warning = device.data_quality_note or ""

    def calculate_predicted_refill_date(self):
        """
        Georgio's proprietary refill prediction formula:
        duty_cycle          = spray_on / (spray_on + spray_off)
        ml_per_op_day       = k_value * duty_cycle * hours_per_day
        ml_per_calendar_day = ml_per_op_day * (days_per_week / 7)
        days_to_empty       = tank_ml / ml_per_calendar_day
        predicted_refill    = last_refill_date + days_to_empty

        Verified test case (A300):
        k=2.5835, ON=20s, OFF=60s, 10hr/day, 5d/week, 200mL tank
        → duty=0.25, mL/op-day=6.46, mL/cal-day=4.61, days=~43
        """
        if not all([self.device_model, self.last_refill_date,
                    self.spray_on_seconds, self.spray_off_seconds,
                    self.hours_per_day, self.days_per_week]):
            return

        device = frappe.get_doc("Aroma Device", self.device_model)

        if not device.k_value or not device.tank_size_ml:
            return

        duty_cycle = self.spray_on_seconds / (self.spray_on_seconds + self.spray_off_seconds)
        ml_per_op_day = device.k_value * duty_cycle * self.hours_per_day
        ml_per_calendar_day = ml_per_op_day * (self.days_per_week / 7)

        if ml_per_calendar_day <= 0:
            return

        days_to_empty = device.tank_size_ml / ml_per_calendar_day
        self.predicted_refill_date = add_days(self.last_refill_date, floor(days_to_empty))
