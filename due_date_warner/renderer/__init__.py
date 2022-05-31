from enum import Enum


class DayCategory(Enum):
    over_due = 0
    urgent = 1
    soon = 2
    later = 3


def get_date_category(days_left: int,
                      urgent_days: int = 14,
                      soon_days: int = 14
                      ) -> DayCategory:

    if days_left < 0:
        return DayCategory.over_due
    if days_left <= urgent_days:
        return DayCategory.urgent
    if days_left <= urgent_days + soon_days:
        return DayCategory.soon
    return DayCategory.later
