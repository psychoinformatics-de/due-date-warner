from datetime import datetime
from typing import List, Tuple

from . import DayCategory, get_date_category


def show_result(due_items: List[Tuple[datetime, str, str, str, str]],
                urgent_days: int = 14,
                soon_days: int = 30,
                ) -> None:

    for entry in sorted(due_items):

        due_time, project, item, item_url, project_url = entry
        now = datetime.now(tz=due_time.tzinfo)
        days_left = (due_time - now).days

        date_string = due_time.strftime("%Y-%m-%d")
        category = get_date_category(days_left, urgent_days, soon_days)
        if category in (DayCategory.over_due, DayCategory.urgent):
            date_string = "**" + date_string + "**"

        print(
            date_string + " --- *" + item + "* - [" + project + "](" +
            project_url + ")  ")
