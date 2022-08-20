from aiogram.dispatcher.filters.callback_data import CallbackData

from typing import Optional


class DepartmentsCallbackFactory(CallbackData, prefix="departments"):
    action: str
    department_id: Optional[int]
