

query_due = """
query due_items($organizationName: String!, $projectCursor: String, $itemCursor: String) {
    organization(login: $organizationName) {
        projectsNext(first: 100, after: $projectCursor) {
            edges {
                cursor
                node {
                    title
                    url
                    items(first: 2, after: $itemCursor) {
                        edges {
                            cursor
                            node {
                                title
                                content {
                                    ... on Issue {
                                        url
                                    }
                                    ... on PullRequest {
                                        url
                                    }
                                }
                                type
                                fieldValues(first: 20) {
                                    nodes {
                                        projectField {name} 
                                        value
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
            totalCount
        }
    }
}
"""


query_projects = """
query projects($organizationName: String!, $projectCursor: String) {
    organization(login: $organizationName) {
        projectsNext(first: 100, after: $projectCursor) {
            edges {
                cursor
                node {
                    id
                    title
                    url
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


query_item = """
query item($projectId: ID!, $itemCursor: String) {
    node(id: $projectId) {
        ... on ProjectNext {
            items(first: 100, after: $itemCursor) {
                edges {
                    cursor
                    node {
                        title
                        content {
                            ... on Issue {
                                url
                            }
                            ... on PullRequest {
                                url
                            }
                        }
                        type
                        fieldValues(first: 100) {
                            nodes {
                                projectField {
                                    name
                                }
                                value
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
