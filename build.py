"""Builds the static site into _site/ for GitHub Pages.

Every page is a Jinja2 template rendered once at build time; each URL
becomes a folder with an index.html, so /resume, /sports/fenerbahce, ...
keep working. The project list is fetched from the GitHub API during the
build (the deploy workflow also runs daily to refresh it).

    python build.py                      # build into _site/
    python -m http.server -d _site 8000  # preview at http://localhost:8000
"""

import json
import os
import shutil
import urllib.request
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).parent
OUT = ROOT / "_site"
GITHUB_USER = "bbzorba"

env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=True)


def load_json(name):
    with open(ROOT / "data" / name, encoding="utf-8") as f:
        return json.load(f)


def github_repos():
    req = urllib.request.Request(f"https://api.github.com/users/{GITHUB_USER}/repos",
                                 headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def render(url, template, **context):
    out = OUT / url.strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(env.get_template(template).render(**context), encoding="utf-8")
    print(f"  {url:30} <- {template}")


def main():
    cv = load_json("cv_data.json")
    posts = load_json("blog_posts.json")
    for key in ("lived", "visited", "want_to_go"):
        posts.setdefault(key, [])

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "static", OUT / "static")
    shutil.copy(ROOT / "static" / "favicon.ico", OUT / "favicon.ico")

    render("/", "home.html")
    render("/resume", "resume.html",
           experiences=cv.get("Experience", []),
           education=cv.get("Education", []),
           skills={
               "Programming": cv.get("Programming Skills", []),
               "Tools": cv.get("Tools", []),
               "Languages": cv.get("Languages", []),
           },
           certificates=cv.get("Certificates", []),
           projects=cv.get("Projects", []),
           areas_of_interest=cv.get("Areas of Interest", {}),
           journal_papers=cv.get("Journal Papers", []),
           conference_proceedings=cv.get("Conference Proceedings", []))
    render("/travel_blog", "blog.html", posts=posts)
    render("/my_projects", "my_projects.html", repos=github_repos())
    render("/live", "live.html")
    render("/contact", "contact.html")
    render("/sports", "sports.html")
    for team in ("fenerbahce", "fenerbahce_beko", "fcbayern", "fcbayern_basketball"):
        render(f"/sports/{team}", f"{team}.html")

    # GitHub Pages: serve files as they are, no Jekyll processing
    (OUT / ".nojekyll").touch()
    print(f"Built into {OUT}")


if __name__ == "__main__":
    main()
