# bbzorba.github.io

Personal website of Barış Berk Zorba: résumé, projects, the hardware I use,
drones, a live view of my home lab, travel, sports and contact pages.

| Document | Content |
|---|---|
| this README | edit, preview, add content, deploy |
| [ARCHITECTURE.md](ARCHITECTURE.md) | how the site is built, deployed and fed with live data |

- **Live:** https://bbzorba.github.io
- **Stack:** static HTML generated from Jinja2 templates (`templates/`),
  content in `data/*.json`, assets in `static/`

## 1. Edit and preview

```bash
pip install -r requirements.txt
python build.py                      # renders every page into _site/
python -m http.server -d _site 8000  # preview at http://localhost:8000
```

## 2. Adding content

| What | Where |
|---|---|
| CV | `data/cv_data.json` |
| A board on the Hardware page | `data/hardware.json` |
| A project group or title | `data/projects.json` (unlisted repos show under "Other projects") |
| Travel post | `data/blog_posts.json` |
| A page | `templates/<name>.html` extending `base.html`, a `render(...)` line in `build.py`, a link in the `links` list in `templates/base.html` |

## 3. Deployment

`.github/workflows/pages.yml` builds the site and publishes it to GitHub
Pages on every push to `main`. It also runs daily, because "My Projects" is
generated from the GitHub API at build time.

Repository settings this needs (once): the repo is named
`bbzorba.github.io`, and Settings → Pages → Source is "GitHub Actions".

## 4. Testing

- Preview locally (above) and click through every page.
- After a push: the Actions run is green and https://bbzorba.github.io
  shows the change within about a minute.
- Live Lab shows "Live" and values updating every 10 s while the hub runs.
- Contact form: send a test message (the first one triggers FormSubmit's
  one-time activation e-mail).

The site used to run as a FastAPI app on Render; that version is in the git
history (before the switch to GitHub Pages).
