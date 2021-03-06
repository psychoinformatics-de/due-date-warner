from datetime import datetime
from typing import List, Tuple

import colorama
from prettytable import PrettyTable

from . import DayCategory, get_date_category


colorama.init()


console_table_headers = [
    "Due date",
    "Item",
    "Project",
]


category_to_colorama = {
    DayCategory.over_due: (colorama.Fore.BLACK, colorama.Back.RED),
    DayCategory.urgent: (colorama.Fore.RED, ""),
    DayCategory.soon: (colorama.Fore.YELLOW, ""),
    DayCategory.later: (colorama.Fore.GREEN, "")
}


def limit_string(string: str, max_length: int) -> str:
    if len(string) < max_length:
        return string + (" " * (max_length - len(string)))
    return string[:max_length - 4] + " ..." \
           if len(string) >= max_length \
           else string


def show_result(due_items: List[Tuple[datetime, str, str, str, str]],
                urgent_days: int = 14,
                soon_days: int = 30,
                ) -> None:

    reset = colorama.Style.RESET_ALL
    table = PrettyTable()
    table.field_names = console_table_headers

    table.align = "l"
    for entry in sorted(due_items):

        due_time, project, item, item_url, project_url = entry
        now = datetime.now(tz=due_time.tzinfo)
        days_left = (due_time - now).days

        fg, bg = category_to_colorama[
            get_date_category(days_left, urgent_days, soon_days)]

        table.add_row([
            fg + bg + due_time.strftime("%Y-%m-%d") + reset,
            limit_string(item, 40) + " (" + item_url + ")" if item_url else item,
            limit_string(project, 40) + " (" + project_url + ")"
        ])

    print(table)
