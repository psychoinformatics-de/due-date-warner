import argparse
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import colorama
from prettytable import PrettyTable
from python_graphql_client import GraphqlClient

from .query_due import query_due


logger = logging.getLogger(__name__)

token_env_name = "GITHUB_AUTH_TOKEN"

default_organization = "psychoinformatics-de"

# TODO: this does not seem "stable", check for a service point that
#  translates the returned values to stati.
github_done_status = "98236657"


colorama.init()


argument_parser = argparse.ArgumentParser(
    description="The project item status tool. Given a github organization "
                "name, this tool will check the top-level projects list and "
                "print a list of all items that have a due date")

argument_parser.add_argument(
    'organization',
    nargs="?",
    default=default_organization,
    help="The name of the github organization that holds the projects that "
         f"should be checked for due items. (default: {default_organization})")

argument_parser.add_argument(
    "--max-days-to-check", "-m",
    type=int,
    default=60,
    help="Define the maximum number of days in the future for which due dates "
         "will be listed. (default: 60)"
)

argument_parser.add_argument(
    "--html-output",
    action="store_true",
    default=False,
    help="Emit an html table"
)


table_headers = [
        "Due date",
        "Project",
        "Item description",
        "Item or Project URL",
        "Project URL"
]


colorama_to_html = {
    colorama.Fore.BLACK: "black",
    colorama.Back.RED: "red",
    colorama.Fore.RED: "red",
    colorama.Fore.YELLOW: "yellow",
    colorama.Fore.GREEN: "green",
}


def get_date_color(days_left: int) -> Tuple[str, str]:
    if days_left < 0:
        return colorama.Fore.BLACK, colorama.Back.RED
    if days_left <= 14:
        return colorama.Fore.RED, ""
    if days_left <= 30:
        return colorama.Fore.YELLOW, ""
    return colorama.Fore.GREEN, ""


def limit_string(string: str, max_length: int) -> str:
    return string[:max_length - 3] + "..." \
           if len(string) >= max_length \
           else string


def show_result(due_items: List[Tuple[datetime, str, str, str, str]],
                max_days_to_check: int,
                html_output: bool
                ) -> None:
    if html_output is False:
        show_text_result(due_items, max_days_to_check)
    else:
        show_html_result(due_items, max_days_to_check)


def show_html_result(due_items: List[Tuple[datetime, str, str, str, str]],
                     max_days_to_check: int
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

        if max_days_to_check < days_left:
            continue

        fg, bg = get_date_color(days_left)
        if bg:
            fg = colorama.Fore.RED

        for index, content in enumerate([due_time.strftime("%Y-%m-%d"),
                                         project,
                                         item,
                                         item_url,
                                         project_url]):
            if index == 0:
                if days_left < 0:
                    content = "**" + content + "**"
                print(f'   <td><font color="{colorama_to_html[fg]}">{content}</font></td>')
            else:
                print_cell(content)

        print("  </tr>")

    print("</table>")


def show_text_result(due_items: List[Tuple[datetime, str, str, str, str]],
                     max_days_to_check: int
                     ) -> None:

    reset = colorama.Style.RESET_ALL
    table = PrettyTable()
    table.field_names = table_headers

    table.align = "l"
    table.align["Item"] = "r"

    for entry in sorted(due_items):

        due_time, project, item, item_url, project_url = entry
        now = datetime.now(tz=due_time.tzinfo)
        days_left = (due_time - now).days

        if max_days_to_check < days_left:
            continue

        fg, bg = get_date_color(days_left)
        table.add_row([
            fg + bg + due_time.strftime("%Y-%m-%d") + reset,
            limit_string(project, 30),
            limit_string(item, 40),
            item_url,
            project_url
        ])

    print(table)


def process_page_info(page_info: Dict) -> Tuple[bool, Optional[str]]:
    if page_info["hasNextPage"] is False:
        return False, None
    return True, page_info["endCursor"]


def get_item_pagination_info(data: Dict) -> Tuple[bool, Optional[str]]:
    return process_page_info(data["data"]["node"]["items"]["pageInfo"])


def get_project_pagination_info(data: Dict) -> Tuple[bool, Optional[str]]:
    return process_page_info(data["data"]["organization"]["projectsNext"]["pageInfo"])


def process_item(item: Dict,
                 project_title: str,
                 project_url: str
                 ) -> List:

    fields = {
        field["projectField"]["name"]: field["value"]
        for field in item["fieldValues"]["nodes"]
    }
    if fields.get("Status") == github_done_status:
        return []
    if "Due" not in fields:
        return []

    due_date = datetime.fromisoformat(fields["Due"])

    url = project_url
    if item["type"] in ("ISSUE", "PULL_REQUEST"):
        if item["content"] is not None:
            url = item["content"]["url"]
        else:
            logger.warning(
                f"can not read content of issue '{item['title']}' "
                f"of project '{project_title}' ({project_url}), is the "
                "token authorized?")
    else:
        url = project_url

    return [(
        due_date,
        project_title,
        item["title"],
        url,
        project_url
    )]


def process_project(project_holder: Dict
                    ) -> List:

    if project_holder is None:
        raise RuntimeError(
            "Can not retrieve project info, is the token authorized?")
    project = project_holder["node"]

    title, url = project["title"], project["url"]

    due_items = []
    for item in project["items"]["edges"]:
        due_items.extend(process_item(item["node"], title, url))
    return due_items


def read_due_items(client: GraphqlClient,
                   organization: str
                   ) -> List[Tuple[datetime, str, str, str, str]]:

    project_cursor = None
    item_cursor = None

    result = client.execute(
        query=query_due,
        variables={
            "organizationName": organization,
            "projectCursor": project_cursor,
            "itemCursor": item_cursor
        }
    )

    due_items = []
    for project in result["data"]["organization"]["projectsNext"]["edges"]:
        due_items.extend(process_project(project))

    return due_items


def cli():

    arguments = argument_parser.parse_args()

    token = os.environ.get(token_env_name, None)
    if token is None:
        print(
            f"Please set the environment variable {token_env_name} to contain"
            " a github authorization token that has access to projects.",
            file=sys.stderr)
        exit(1)

    client = GraphqlClient(
        endpoint="https://api.github.com/graphql",
        headers={"Authorization": f"token {token}"})

    due_items = read_due_items(client, arguments.organization)

    if len(due_items) == 0:
        print("No items with due times were found.")
    else:
        show_result(
            due_items,
            arguments.max_days_to_check,
            arguments.html_output)
