

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
                                    nodes {
                                        projectField {name} 
                                        value
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
