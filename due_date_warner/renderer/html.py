from datetime import datetime
from typing import List, Tuple


from . import DayCategory, get_date_category, table_headers


category_to_html = {
    DayCategory.over_due: "darkred",
    DayCategory.urgent: "red",
    DayCategory.soon: "yellow",
    DayCategory.later: "green",
}


def show_result(due_items: List[Tuple[datetime, str, str, str, str]],
                urgent_days: int = 14,
                soon_days: int = 30,
                ) -> None:

    def print_cell(content: str, tag: str = "td"):
        print(f"    <{tag}>{content}</{tag}>")

    print("<table>")
    print("  <tr>")
    for header in table_headers:
        print_cell(header, "th")
    print("  </tr>")

    for entry in sorted(due_items):
        print("  <tr>")

        due_time, project, item, item_url, project_url = entry
        now = datetime.now(tz=due_time.tzinfo)
        days_left = (due_time - now).days

        category = get_date_category(days_left, urgent_days, soon_days)
        print(
            f'   <td><font color="{category_to_html[category]}">'
            f'{due_time.strftime("%Y-%m-%d")}</font></td>')

        for content in [project, item, item_url, project_url]:
            print_cell(content)

        print("  </tr>")
    print("</table>")
