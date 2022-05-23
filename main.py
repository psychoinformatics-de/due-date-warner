import argparse
import os
import sys
from datetime import datetime
from typing import List, Tuple

import colorama
from prettytable import PrettyTable
from python_graphql_client import GraphqlClient

from query_due import query_due


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
                arguments: argparse.Namespace
                ) -> None:
    if arguments.html_output is False:
        show_text_result(due_items, arguments)
    else:
        show_html_result(due_items, arguments)


def show_html_result(due_items: List[Tuple[datetime, str, int, str, str, str]],
                     arguments: argparse.Namespace
                     ) -> None:

    def print_cell(content: str):
        print(f"    <td>{content}</td>")

    print("<table>")

    for entry in sorted(due_items):
        print("  <tr>")

        due_time, project, item_index, item, item_url, project_url = entry
        now = datetime.now(tz=due_time.tzinfo)
        days_left = (due_time - now).days

        if arguments.max_days_to_check < days_left:
            continue

        fg, bg = get_date_color(days_left)

        for content in [due_time.strftime("%Y-%m-%d"),
                        limit_string(project, 30),
                        item_index,
                        limit_string(item, 40),
                        item_url,
                        project_url]:
            print_cell(content)
        print("  </tr>")

    print("</table>")


def show_text_result(due_items: List[Tuple[datetime, str, int, str, str, str]],
                arguments: argparse.Namespace
                ) -> None:

    reset = colorama.Style.RESET_ALL
    table = PrettyTable()
    table.field_names = [
        "Due date",
        "Project",
        "Item",
        "Item description",
        "Item or Project URL",
        "Project URL"]

    table.align = "l"
    table.align["Item"] = "r"

    for entry in sorted(due_items):

        due_time, project, item_index, item, item_url, project_url = entry
        now = datetime.now(tz=due_time.tzinfo)
        days_left = (due_time - now).days

        if arguments.max_days_to_check < days_left:
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


def read_due_items(token: str,
                   arguments: argparse.Namespace
                   ) -> List[Tuple[datetime, str, int, str, str, str]]:

    client = GraphqlClient(
        endpoint="https://api.github.com/graphql",
        headers={"Authorization": f"token {token}"})

    results = client.execute(
        query=query_due,
        variables={
            "organizationName": arguments.organization
        })

    due_items = []
    for project in results["data"]["organization"]["projectsNext"]["nodes"]:
        for item_index, edge in enumerate(project["items"]["edges"]):
            node = edge["node"]
            if node["type"] in ("ISSUE", "PULL_REQUEST"):
                url = node["content"]["url"]
            else:
                url = project["url"]
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
                project["title"],
                item_index + 1,
                item_title,
                url,
                project["url"]))

    return due_items


def main():

    arguments = argument_parser.parse_args()

    token = os.environ.get(token_env_name, None)
    if token is None:
        print(
            f"Please set the environment variable {token_env_name} to contain"
            " a github authorization token that has access to projects.",
            file=sys.stderr)
        exit(1)

    due_items = read_due_items(token, arguments)

    if len(due_items) == 0:
        print("No items with due times were found.")
    else:
        show_result(due_items, arguments)


if __name__ == '__main__':
    main()
