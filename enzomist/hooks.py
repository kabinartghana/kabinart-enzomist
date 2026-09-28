app_name = "enzomist"
app_title = "Enzomist"
app_publisher = "Kabinart Ghana Ltd"
app_description = "Enzomist custom ERPNext app — commercial aroma diffuser management"
app_email = "joseph@kabinartghana.com"
app_license = "MIT"
app_version = "0.0.1"

# Document Events
# Device Refill.on_submit is defined on the DocType class itself —
# no doc_events hook needed (the old hook pointed to a function that did not exist).

# Scheduled Tasks
scheduler_events = {
    "daily": [
        "enzomist.tasks.check_refill_alerts"
    ]
}

# Fixtures — export these doctypes with bench export-fixtures
fixtures = [
    {"dt": "Custom Field"},
    {"dt": "Property Setter"},
]
