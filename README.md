# Due Date Warning Tool

This tool will sift through all beta-projects that exist for a github organization, look for all items with a due-date, i.e. a value field with name "Due" and type "Date", and print a table of the items that are due within a given number of days (by default: 60). The output can either be colored text or HTML (the supported HTML version is HTML 4 in order to be able to use the tool's output with the `/html` command in Matrix).

## Installation:

1. Create and activate a virtual environment (recommended, but not required)

```shell
python -m venv $HOME/venv/due-date-warner
source $HOME/venv/due-date-warner/bin/activate
```

2. Install the due date warning tool

```shell
github clone https://github.com/psychoinformatics-de/due-date-warner.git
cd due-date-warner
pip install .
```

## Usage

You need to provide a github authorization token that is authorized to read the projects of the organization that the due-date-warner should examine. The github authorization token has to be provided in the environment variable `GITHUB_AUTH_TOKEN`. For example, if your github authorization token is `ghp_als3mnmnsdf44sdfsdfmndsfsdfhehusdfZ`, you can use the following command to set the environment variable:

```
export GITHUB_AUTH_TOKEN="ghp_als3mnmnsdf44sdfsdfmndsfsdfhehusdfZ4"
```

By default the due-date-warner will search through the beta-project of the organization `psychoinformatics-de`. Provide your own organization in the command line. 
```shell
ddw psychoinformatics-de
```
It will print out a table with all project items that have a due date, are not done and within the next 60 days.

