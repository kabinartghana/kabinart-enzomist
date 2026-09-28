import frappe
from frappe.utils import today, add_days, getdate

def check_refill_alerts():
    """
    Daily scheduled task.
    Checks all active placements where alert is enabled.
    If predicted_refill_date is within alert_days_before days,
    sends an internal email alert to the Enzomist team.
    No email is sent to the client automatically.
    """
    placements = frappe.get_all(
        "Device Placement",
        filters={"alert_enabled": 1, "predicted_refill_date": ["!=", ""]},
        fields=["name", "customer", "device_model", "scent_oil_item",
                "predicted_refill_date", "alert_days_before"]
    )

    alerts_to_send = []
    for p in placements:
        if not p.predicted_refill_date:
            continue
        days_remaining = (getdate(p.predicted_refill_date) - getdate(today())).days
        if 0 <= days_remaining <= (p.alert_days_before or 7):
            alerts_to_send.append(p)

    if not alerts_to_send:
        return

    # Build alert email
    rows = ""
    for p in alerts_to_send:
        days_remaining = (getdate(p.predicted_refill_date) - getdate(today())).days
        rows += f"""
        <tr>
            <td>{p.customer}</td>
            <td>{p.device_model}</td>
            <td>{p.scent_oil_item}</td>
            <td>{p.predicted_refill_date}</td>
            <td><strong>{days_remaining} days</strong></td>
        </tr>"""

    message = f"""
    <h3>Enzomist Refill Alerts — {today()}</h3>
    <p>The following placements are due for a refill soon:</p>
    <table border="1" cellpadding="6" cellspacing="0">
        <tr>
            <th>Client</th>
            <th>Device</th>
            <th>Scent</th>
            <th>Predicted Refill Date</th>
            <th>Days Remaining</th>
        </tr>
        {rows}
    </table>
    <p><em>This is an internal alert only. No email has been sent to the client.</em></p>
    """

    # Send to System Manager / Georgio
    recipients = frappe.get_all(
        "User",
        filters={"role_profile_name": ["in", ["System Manager", "Sales User"]], "enabled": 1},
        pluck="email"
    )

    if recipients:
        frappe.sendmail(
            recipients=list(set(recipients)),
            subject=f"[Enzomist] {len(alerts_to_send)} Refill(s) Due Soon — {today()}",
            message=message
        )
