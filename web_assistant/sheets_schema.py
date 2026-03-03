HEADERS = [
    "lead_id",
    "created_at_utc",
    "created_at_local",
    "source",
    "source_user_id",
    "source_username",
    "name",
    "telegram_username",
    "phone",
    "contact_ok",
    "preferred_contact_method",
    "request",
    "status",
    "priority",
    "utm_source",
    "utm_campaign",
    "manager_note",
    "last_update_at_utc",
]


EMAIL_IN_SHARED_COLUMN_NOTE = (
    "For website leads, email is stored in column H (telegram_username) with prefix 'email:' "
    "to keep the shared A:R schema compatible with Telegram bot."
)
