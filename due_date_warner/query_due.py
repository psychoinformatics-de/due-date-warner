

query_due = """
query due_items($organizationName: String!, $projectCursor: String, $itemCursor: String) {
    organization(login: $organizationName) {
        projectsNext(first: 100, after: $projectCursor) {
            edges {
                cursor
                node {
                    title
                    url
                    items(first: 100, after: $itemCursor) {
                        edges {
                            cursor
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
                                        cursor
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
query next_field($itemId: ID!, $endCursor: String!) {
    node(id: $itemId) {
        ... on ProjectNextItem {
            id
            fieldValues(first: 100, after: $endCursor) {
                edges {
                    cursor
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
