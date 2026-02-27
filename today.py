#!/usr/bin/env python3
"""Fetch GitHub stats and update profile SVGs."""

import os
import re
import time
import requests

USERNAME = os.environ.get("USER_NAME", "toqitahamid")
TOKEN = os.environ["ACCESS_TOKEN"]
GRAPHQL_URL = "https://api.github.com/graphql"


def graphql(query, variables=None):
    """Execute a GitHub GraphQL query."""
    resp = requests.post(
        GRAPHQL_URL,
        json={"query": query, "variables": variables or {}},
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    return data["data"]


def fetch_user_info():
    """Get repos, stars, followers, and contribution years."""
    query = """
    query($login: String!) {
        user(login: $login) {
            repositories(ownerAffiliations: OWNER, first: 100, orderBy: {field: STARGAZERS, direction: DESC}) {
                totalCount
                nodes { name isFork stargazerCount }
            }
            followers { totalCount }
            contributionsCollection { contributionYears }
        }
    }
    """
    data = graphql(query, {"login": USERNAME})
    user = data["user"]
    repos = user["repositories"]["nodes"]
    return {
        "repos": user["repositories"]["totalCount"],
        "stars": sum(n["stargazerCount"] for n in repos),
        "followers": user["followers"]["totalCount"],
        "years": user["contributionsCollection"]["contributionYears"],
        "repo_names": [n["name"] for n in repos if not n["isFork"]],
    }


def fetch_total_commits(years):
    """Get total commits across all contribution years using aliases."""
    if not years:
        return 0

    fragments = []
    for year in years:
        start = f"{year}-01-01T00:00:00Z"
        end = f"{year}-12-31T23:59:59Z"
        fragments.append(
            f'y{year}: contributionsCollection(from: "{start}", to: "{end}") '
            f"{{ totalCommitContributions restrictedContributionsCount }}"
        )

    query = (
        "query($login: String!) {\n"
        "  user(login: $login) {\n"
        "    " + "\n    ".join(fragments) + "\n"
        "  }\n"
        "}"
    )
    data = graphql(query, {"login": USERNAME})
    user = data["user"]

    total = 0
    for year in years:
        c = user[f"y{year}"]
        total += c["totalCommitContributions"] + c["restrictedContributionsCount"]
    return total


def fetch_loc(repo_names):
    """Get total lines of code (additions) across owned non-fork repos."""
    total = 0
    headers = {"Authorization": f"Bearer {TOKEN}"}

    for name in repo_names:
        url = f"https://api.github.com/repos/{USERNAME}/{name}/stats/contributors"
        for _ in range(3):
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                for contributor in resp.json():
                    if (
                        contributor.get("author")
                        and contributor["author"]["login"].lower() == USERNAME.lower()
                    ):
                        total += sum(w["a"] for w in contributor["weeks"])
                break
            elif resp.status_code == 202:
                time.sleep(2)
            else:
                break

    return total


def update_svg(filepath, stats):
    """Update SVG stat elements by their id attributes using regex."""
    with open(filepath, "r") as f:
        content = f.read()

    for key, value in stats.items():
        formatted = f"{value:,}"
        pattern = rf'(id="{key}_data">)[^<]*(</tspan>)'
        content = re.sub(pattern, rf"\g<1>{formatted}\2", content)

    with open(filepath, "w") as f:
        f.write(content)


def main():
    info = fetch_user_info()
    commits = fetch_total_commits(info["years"])
    loc = fetch_loc(info["repo_names"])

    stats = {
        "repos": info["repos"],
        "stars": info["stars"],
        "commits": commits,
        "followers": info["followers"],
        "loc": loc,
    }

    for key, value in stats.items():
        print(f"  {key}: {value:,}")

    for svg in ["dark_mode.svg", "light_mode.svg"]:
        update_svg(svg, stats)
        print(f"  Updated {svg}")


if __name__ == "__main__":
    main()
