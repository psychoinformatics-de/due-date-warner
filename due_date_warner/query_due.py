

query_due = """
query due_items($organizationName: String!) {
    organization(login: $organizationName) {
        id
        projectsNext(first: 100) {
            edges {
                node {
                    id
                    title
                    url
                    items(first: 100) {
                        edges {
                            node {
                                id
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
                                fieldValues(first: 48) {
                                    edges {
                                        node {
                                            projectField {name} 
                                            value
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
            pageInfo {
                endCursor
                hasNextPage
            }
        }
    }
}
"""


query_field_values = """
query next_fields($nodeId: ID!, $endCursor: String!) {
    node(id: $nodeId) {
        ... on ProjectNextItem {
            id
            fieldValues(first: 100, after: $endCursor) {
                edges {
                    node {
                        projectField {name} 
                        value
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


query_item_values = """
query next_items($nodeId: ID!, $endCursor: String!) {
    node(id: $nodeId) {
        ... on ProjectNext {
            id
            title
            url
            items(first: 100, after: $endCursor) {
                edges {
                    node {
                        id
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
                            edges {
                                node {
                                    projectField {name} 
                                    value
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


query_projects = """
query next_project($nodeId: ID!, $endCursor: String) {
    node(id: $nodeId) {
        ... on Organization {
            id
            projectsNext(first: 100, after: $endCursor) {
                edges {
                    node {
                        id
                        title
                        url
                        items(first: 100) {
                            edges {
                                node {
                                    id
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
                                    fieldValues(first: 48) {
                                        edges {
                                            node {
                                                projectField {name} 
                                                value
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
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }
}
"""
