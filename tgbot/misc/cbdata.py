from aiogram.dispatcher.filters.callback_data import CallbackData

from typing import Union, Optional


class MainCallbackFactory(CallbackData, prefix="main"):
    category: str
    action: Optional[str]
    data: Union[int, str, None]
