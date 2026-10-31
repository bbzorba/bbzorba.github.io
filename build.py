"""Builds the static site into _site/ for GitHub Pages.

Every page is a Jinja2 template rendered once at build time; each URL
becomes a folder with an index.html, so /resume, /sports/fenerbahce, ...
keep working. Content lives in data/*.json. The project list combines
data/projects.json (grouping, titles) with live data from the GitHub API
(the deploy workflow also runs daily to pick up new repositories).

    python build.py                      # build into _site/
    python -m http.server -d _site 8000  # preview at http://localhost:8000
"""

import json
import os
import shutil
import time
import urllib.request
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).parent
OUT = ROOT / "_site"
GITHUB_USER = "bbzorba"

env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=True)
# Appended to asset URLs so browsers fetch fresh CSS after every deploy
env.globals["build_id"] = str(int(time.time()))


def load_json(name):
    with open(ROOT / "data" / name, encoding="utf-8") as f:
        return json.load(f)


def github_repos():
    req = urllib.request.Request(
        f"https://api.github.com/users/{GITHUB_USER}/repos?per_page=100&sort=pushed",
        headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def project_groups():
    """Groups from data/projects.json, filled in with live GitHub data.

    Repositories that no longer exist are dropped; new ones without a group
    land in "Other projects".
    """
    config = load_json("projects.json")
    repos = {r["name"]: r for r in github_repos()}
    groups = []

    for group in config["groups"]:
        projects = []
        for p in group["projects"]:
            repo = repos.pop(p["repo"], None)
            if repo is None:
                continue
            projects.append({**p, "url": repo["html_url"], "language": repo["language"],
                             "updated": repo["pushed_at"][:10], "stars": repo["stargazers_count"]})
        if projects:
            groups.append({**group, "projects": projects})

    if repos:
        groups.append({
            "name": "Other projects", "icon": "📦", "blurb": "Not grouped yet.",
            "projects": [{"repo": r["name"], "title": r["name"].replace("-", " ").replace("_", " "),
                          "summary": r["description"] or "", "url": r["html_url"],
                          "language": r["language"], "updated": r["pushed_at"][:10],
                          "stars": r["stargazers_count"]} for r in repos.values()],
        })
    return config["intro"], groups


def render(url, template, **context):
    out = OUT / url.strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(env.get_template(template).render(page=url, **context), encoding="utf-8")
    print(f"  {url:30} <- {template}")


def main():
    cv = load_json("cv_data.json")
    posts = load_json("blog_posts.json")
    for key in ("lived", "visited", "want_to_go"):
        posts.setdefault(key, [])
    intro, groups = project_groups()

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "static", OUT / "static")
    shutil.copy(ROOT / "static" / "favicon.ico", OUT / "favicon.ico")

    render("/", "home.html", cv=cv)
    render("/resume", "resume.html", cv=cv)
    render("/my_projects", "my_projects.html", intro=intro, groups=groups)
    render("/hardware", "hardware.html", hw=load_json("hardware.json"))
    render("/drones", "drones.html")
    render("/live", "live.html")
    render("/travel_blog", "blog.html", posts=posts)
    render("/contact", "contact.html")
    render("/sports", "sports.html")
    for team in ("fenerbahce", "fenerbahce_beko", "fcbayern", "fcbayern_basketball"):
        render(f"/sports/{team}", f"{team}.html")

    # GitHub Pages: serve files as they are, no Jekyll processing
    (OUT / ".nojekyll").touch()
    print(f"Built into {OUT}")


if __name__ == "__main__":
    main()
