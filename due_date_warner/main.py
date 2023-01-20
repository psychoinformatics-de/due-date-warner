import argparse
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime
from importlib import import_module
from typing import Dict, Iterable, List, Optional, Tuple

from python_graphql_client import GraphqlClient

from .query_due import query_due, query_item_values, query_projects


logger = logging.getLogger(__name__)

token_env_name = "GITHUB_AUTH_TOKEN"

default_organization = "psychoinformatics-de"

# TODO: this does not seem "stable", check for a service point that
#  translates the returned values to stati.
github_done_status = "98236657"


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
         "will be listed. (default: 60)")

argument_parser.add_argument(
    "--renderer",
    type=str,
    default="console",
    help="Choose the renderer for the resulting list. The renderer is a module"
         "in the package due_date_warner.renderer, which implements a method"
         "called 'show_result', e.g. use '--renderer=html' to use the module"
         "html.py for rendering. Currently three renderer are supported: "
         "'console', 'markup', and 'html'. (default: 'console')")

argument_parser.add_argument(
    "--days-urgent",
    type=int,
    default=14,
    help="Number of days from today for which the "
         "output will be marked 'urgent'. (default: 14)")

argument_parser.add_argument(
    "--days-soon",
    type=int,
    default=14,
    help="Number of days from today + 'urgent' days for which the "
         "output will be marked 'soon', i.e. yellow. (default: 14)")

argument_parser.add_argument(
    "--html-output",
    action="store_true",
    default=False,
    help="Emit an html table. This argument exists for backward compatibility, "
         "it takes precedence over renderer via '--renderer'. Instead of this "
         "parameter you should use '--renderer=html'.")


def show_result(renderer: str,
                due_items: List[Tuple[datetime, str, str, str, str]],
                urgent_days: int = 14,
                soon_days: int = 30,
                ) -> None:
    render_module = import_module(f"due_date_warner.renderer.{renderer}")
    render_module.show_result(due_items, urgent_days, soon_days)


def process_error(result: Dict):
    errors = result.get("errors")
    if not errors:
        return

    error_types = defaultdict(set)
    for error in errors:
        error_types[error["type"]].add(error["message"])

    raise ValueError(
        "\n".join(
            f"{e_type}: {message}"
            for e_type, message in error_types.items()))


def process_query(client: GraphqlClient,
                  query: str,
                  variables: Optional[Dict] = None
                  ) -> Dict:

    result = client.execute(
        query=query,
        variables=variables or {})

    process_error(result)
    return result


def get_all(initial_node: Dict,
            client: GraphqlClient,
            query: str,
            element_key: str
            ) -> Iterable:

    yield from initial_node[element_key]["edges"]

    node = initial_node
    while node[element_key]["pageInfo"]["hasNextPage"]:
        more_data = process_query(
            client,
            query,
            {
                "nodeId": node["id"],
                "endCursor": node[element_key]["pageInfo"]["endCursor"]})

        node = more_data["data"]["node"]
        yield from node[element_key]["edges"]


def process_item(max_days: int,
                 item: Dict,
                 project_title: str,
                 project_url: str
                 ) -> Iterable:

    field_values = {
        key: value['value'] if (isinstance(value, dict) and value) else value
        for key, value in item.items()
        if value is not None}
    if field_values.get("Status") == github_done_status:
        return
    if "Due" not in field_values:
        return

    due_date = datetime.fromisoformat(field_values["Due"])
    now = datetime.now(tz=due_date.tzinfo)
    days_left = (due_date - now).days
    if days_left > max_days:
        return

    url = project_url
    if item["type"] in ("ISSUE", "PULL_REQUEST"):
        if item["content"] is not None:
            url = item["content"]["value"]
        else:
            logger.warning(
                f"can not read content of issue '{item['title']}' "
                f"of project '{project_title}' ({project_url}). Maybe the token"
                " is not authorized to access the linked issue or PR? That"
                " might be the case if the linked project is private, and your"
                " token does not have the scope 'repo'")
    else:
        url = project_url

    yield due_date, project_title, field_values["Title"], url, project_url


def process_project(client: GraphqlClient,
                    project_holder: Dict,
                    max_days: int
                    ) -> Iterable:

    if project_holder is None:
        raise RuntimeError(
            "Can not retrieve project info, is the token authorized?")

    project = project_holder["node"]
    title, url = project["title"], project["url"]
    for item in get_all(project, client, query_item_values, "items"):
        yield from process_item(max_days, item["node"], title, url)


def read_due_items(client: GraphqlClient,
                   organization: str,
                   max_days: int
                   ) -> Iterable[Tuple[datetime, str, str, str, str]]:

    result = process_query(client, query_due, {"organizationName": organization})
    project_holder = result["data"]["organization"]
    for project_next in get_all(project_holder, client, query_projects, "projectsV2"):
        yield from process_project(client, project_next, max_days)


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

    due_items = list(
        read_due_items(
            client,
            arguments.organization,
            arguments.max_days_to_check))

    if len(due_items) == 0:
        print(
            f"No items with due times with the next "
            f"{arguments.max_days_to_check} days were found.")
    else:
        show_result(
            arguments.renderer if arguments.html_output is False else "html",
            due_items,
            arguments.days_urgent,
            arguments.days_soon)
