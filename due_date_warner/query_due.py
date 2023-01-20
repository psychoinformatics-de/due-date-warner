

query_due = """
query due_items($organizationName: String!) {
    organization(login: $organizationName) {
        id
        projectsV2(first: 100) {
            edges {
                node {
                    id
                    title
                    url
                    items(first:100) {
                        edges {
                            node {
                                id
                                type
                                content {
                                    ... on Issue {
                                        value: url
                                    }
                                    ... on PullRequest {
                                        value: url
                                    }
                                }
                                Title: fieldValueByName(name: "Title") {
                                    ... on ProjectV2ItemFieldTextValue {
                                        value: text
                                    }
                                }
                                Due: fieldValueByName(name: "Due") {
                                    ... on ProjectV2ItemFieldDateValue {
                                        value: date
                                    }
                                }
                                Status: fieldValueByName(name: "Status") {
                                    ... on ProjectV2ItemFieldSingleSelectValue {
                                        value: optionId
                                    }
                                }
                            }
                        }
                        pageInfo {
                            endCursor
                            hasNextPage
                        }
                    }
                }
            }
            pageInfo {
                endCursor
                hasNextPage
            }
        }
    }
}
"""

query_item_values = """
query next_items($nodeId: ID!, $endCursor: String!) {
    node(id: $nodeId) {
        ... on ProjectsV2 {
            id
            title
            url
            items(first:100 after: $endCursor) {
                edges {
                    node {
                        id
                        type
                        content {
                            ... on Issue {
                                Url: url
                            }
                            ... on PullRequest {
                                Url: url
                            }
                        }
                        Title: fieldValueByName(name: "Title") {
                            ... on ProjectV2ItemFieldTextValue {
                                value: text
                            }
                        }
                        Due: fieldValueByName(name: "Due") {
                            ... on ProjectV2ItemFieldDateValue {
                                value: date
                            }
                        }
                        Status: fieldValueByName(name: "Status") {
                            ... on ProjectV2ItemFieldSingleSelectValue {
                                value: optionId
                            }
                        }
                    }
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
    }
}
"""


query_projects = """
query next_project($nodeId: ID!, $endCursor: String) {
    node(id: $nodeId) {
        ... on Organization {
            id
            projectsV2(first: 100, after: $endCursor) {
                edges {
                    node {
                        id
                        title
                        url
                        items(first:100) {
                            edges {
                                node {
                                    id
                                    type
                                    content {
                                        ... on Issue {
                                            Url: url
                                        }
                                        ... on PullRequest {
                                            Url: url
                                        }
                                    }
                                    Title: fieldValueByName(name: "Title") {
                                        ... on ProjectV2ItemFieldTextValue {
                                            value: text
                                        }
                                    }
                                    Due: fieldValueByName(name: "Due") {
                                        ... on ProjectV2ItemFieldDateValue {
                                            value: date
                                        }
                                    }
                                    Status: fieldValueByName(name: "Status") {
                                        ... on ProjectV2ItemFieldSingleSelectValue {
                                            value: optionId
                                        }
                                    }
                                }
                            }
                            pageInfo {
                                endCursor
                                hasNextPage
                            }
                        }
                    }
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }
}
"""
