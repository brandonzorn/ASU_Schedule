from .daily_notify_handlers import daily_time_selection_handler
from .import_document_handler import handle_file
from .registration_handlers import registration_handler
from .schedule_handlers import schedules_table_handler
from .staff_handlers import (
    delete_all_schedules_handler,
    message_handler,
    turn_off_daily_notify_handler,
    users_list_handler,
    users_stats_handler,
)

__all__ = [
    registration_handler,
    schedules_table_handler,
    daily_time_selection_handler,
    message_handler,
    users_list_handler,
    users_stats_handler,
    turn_off_daily_notify_handler,
    delete_all_schedules_handler,
    handle_file,
]
