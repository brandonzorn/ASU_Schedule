from .daily_notify_handlers import notify_time_handler
from .import_document_handler import handle_file
from .registration_handlers import registration_handler
from .schedule_handlers import schedule_table_handler
from .staff_handlers import (
    delete_all_schedules_handler,
    message_handler,
    turn_off_daily_notify_handler,
    users_list_handler,
    users_stats_handler,
    error_handler,
)

__all__ = [
    registration_handler,
    schedule_table_handler,
    notify_time_handler,
    message_handler,
    users_list_handler,
    users_stats_handler,
    turn_off_daily_notify_handler,
    delete_all_schedules_handler,
    handle_file,
    error_handler,
]
