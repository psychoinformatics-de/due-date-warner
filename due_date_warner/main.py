import argparse
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import colorama
from prettytable import PrettyTable
from python_graphql_client import GraphqlClient

from .query_due import query_item, query_projects


token_env_name = "GITHUB_AUTH_TOKEN"

default_organization = "psychoinformatics-de"

# TODO: this does not seem "stable", check for a service point that
#  translates the returned values to stati.
github_done_statue = "98236657"


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
        "Item",
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


def show_result(due_items: List[Tuple[datetime, str, int, str, str, str]],
                max_days_to_check: int,
                html_output: bool
                ) -> None:
    if html_output is False:
        show_text_result(due_items, max_days_to_check)
    else:
        show_html_result(due_items, max_days_to_check)


def show_html_result(due_items: List[Tuple[datetime, str, int, str, str, str]],
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

        due_time, project, item_index, item, item_url, project_url = entry
        now = datetime.now(tz=due_time.tzinfo)
        days_left = (due_time - now).days

        if max_days_to_check < days_left:
            continue

        fg, bg = get_date_color(days_left)
        if bg:
            fg = colorama.Fore.RED

        for index, content in enumerate([due_time.strftime("%Y-%m-%d"),
                                         project,
                                         item_index,
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


def show_text_result(due_items: List[Tuple[datetime, str, int, str, str, str]],
                     max_days_to_check: int
                     ) -> None:

    reset = colorama.Style.RESET_ALL
    table = PrettyTable()
    table.field_names = table_headers

    table.align = "l"
    table.align["Item"] = "r"

    for entry in sorted(due_items):

        due_time, project, item_index, item, item_url, project_url = entry
        now = datetime.now(tz=due_time.tzinfo)
        days_left = (due_time - now).days

        if max_days_to_check < days_left:
            continue

        fg, bg = get_date_color(days_left)
        table.add_row([
            fg + bg + due_time.strftime("%Y-%m-%d") + reset,
            limit_string(project, 30),
            item_index,
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


def read_all_project_ids(client: GraphqlClient,
                         organization: str
                         ) -> List[Tuple[str, str, str]]:

    project_ids = []
    project_cursor = None
    more_projects_to_read = True
    while more_projects_to_read is True:

        result = client.execute(
            query=query_projects,
            variables={
                "organizationName": organization,
                "projectCursor": project_cursor
            })

        for project in result["data"]["organization"]["projectsNext"]["edges"]:
            project_ids.append((
                project["node"]["id"],
                project["node"]["title"],
                project["node"]["url"]))

        more_projects_to_read, project_cursor = get_project_pagination_info(result)
    return project_ids


def read_all_items(client: GraphqlClient,
                   projects: List[Tuple[str, str, str]]
                   ) -> List[Tuple[datetime, str, int, str, str, str]]:

    due_items = []
    for project in projects:

        # Inner loop, read project items
        item_cursor = None
        more_items_to_read = True
        while more_items_to_read is True:

            result = client.execute(
                query=query_item,
                variables={
                    "projectId": project[0],
                    "itemCursor": item_cursor
                })

            for item_index, edge in enumerate(result["data"]["node"]["items"]["edges"]):
                node = edge["node"]
                if node["type"] in ("ISSUE", "PULL_REQUEST"):
                    url = node["content"]["url"]
                else:
                    url = project[2]
                field_values_list = node["fieldValues"]["nodes"]
                due_field_values_list = [
                    field_values
                    for field_values in field_values_list
                    if any(
                        field_values["projectField"]["name"] == "Due"
                        for field_values in field_values_list)]
                if not due_field_values_list:
                    continue

                item_title = [
                    x["value"]
                    for x in due_field_values_list
                    if x["projectField"]["name"] == "Title"][0]

                due = [
                    x["value"]
                    for x in due_field_values_list
                    if x["projectField"]["name"] == "Due"][0]

                status = (
                        [
                            x["value"]
                            for x in due_field_values_list
                            if x["projectField"]["name"] == "Status"
                        ] or [None])[0]

                if status == github_done_statue:
                    continue

                due_items.append((
                    datetime.fromisoformat(due),
                    project[1],
                    item_index + 1,
                    item_title,
                    url,
                    project[2]))

            more_items_to_read, item_cursor = get_item_pagination_info(result)

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

    projects = read_all_project_ids(client, arguments.organization)
    due_items = read_all_items(client, projects)

    if len(due_items) == 0:
        print("No items with due times were found.")
    else:
        show_result(
            due_items,
            arguments.max_days_to_check,
            arguments.html_output)
