

query_due = """
query due_items($organizationName: String!) {
    organization(login: $organizationName) {
        projectsNext(first: 100) {
            nodes {
                title
                url
                items(first: 100) {
                    edges {
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
                }
            }
        }
    }
}
"""
