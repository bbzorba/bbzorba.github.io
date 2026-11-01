# Website architecture

How [bbzorba.github.io](https://bbzorba.github.io) is built, deployed and
fed with live data. Editing, preview and adding content:
[README.md](README.md).

## 1. What we built

The site is fully static: GitHub Pages serves plain HTML, CSS and
JavaScript, and there is no server of my own. Everything dynamic happens
either at **build time** (Python + Jinja2 in GitHub Actions) or in the
**visitor's browser** (live sensor data over MQTT, the contact form).

```mermaid
flowchart LR
    subgraph REPO["GitHub repo bbzorba.github.io"]
        direction TB
        DATA["data/*.json<br/>CV, hardware, project groups, blog"]
        TPL["templates/*.html<br/>Jinja2"]
        STATIC["static/<br/>CSS, images"]
        BUILD["build.py"]
        DATA --> BUILD
        TPL --> BUILD
        STATIC --> BUILD
    end
    GHAPI["GitHub REST API<br/>my repositories"] -->|"at build time"| BUILD
    BUILD -->|"_site/"| ACTIONS["GitHub Actions<br/>pages.yml"]
    ACTIONS -->|deploy| PAGES["GitHub Pages CDN"]
    PAGES -->|"HTML, CSS, JS"| VISITOR["Visitor's browser"]

    subgraph EXT["Third-party services used from the browser"]
        BROKER[("MQTT broker<br/>broker.hivemq.com")]
        FORM["FormSubmit<br/>formsubmit.co"]
    end
    HUB["ESP32-C6 Home Hub<br/>(my home network)"] -->|"MQTT publish every 10 s"| BROKER
    BROKER -->|"WebSocket subscribe"| VISITOR
    VISITOR -->|"contact form POST"| FORM
    FORM -->|e-mail| INBOX["My inbox"]
```

| Page | URL | Content source |
|---|---|---|
| Home | `/` | `templates/home.html` |
| Resume | `/resume` | `data/cv_data.json` |
| Projects | `/my_projects` | `data/projects.json` (groups, titles) + GitHub API (links, languages, dates) |
| Hardware | `/hardware` | `data/hardware.json` |
| Drones | `/drones` | `templates/drones.html` |
| Live Lab | `/live` | MQTT, in the browser |
| Travel | `/travel_blog` | `data/blog_posts.json` |
| Contact | `/contact` | FormSubmit, in the browser |
| Sports | `/sports/...` | templates |

## 2. Build and deploy

```mermaid
sequenceDiagram
    autonumber
    actor Me
    participant GH as GitHub repo
    participant A as GitHub Actions
    participant API as GitHub REST API
    participant P as GitHub Pages

    Me->>GH: git push (or daily 04:00 UTC cron, or "Run workflow")
    GH->>A: start pages.yml
    A->>A: pip install jinja2, python build.py
    A->>API: GET /users/bbzorba/repos
    API-->>A: repositories
    A->>A: group repos (data/projects.json), render all pages to _site/
    A->>P: upload artifact + deploy
    P-->>Me: live in about a minute
```

The daily run picks up new repositories. Any repository not listed in
`data/projects.json` appears under "Other projects" until it gets a group.
Asset URLs carry a build id (`style.css?v=...`) so browsers fetch fresh CSS
after each deploy.

## 3. Live Lab: publish/subscribe

The page subscribes to the hub's MQTT topics straight from the browser
(MQTT.js over secure WebSocket). Both topics are retained, so a visitor
sees the latest values immediately instead of waiting for the next
10-second publish.

```mermaid
sequenceDiagram
    autonumber
    participant V as Visitor's browser
    participant P as GitHub Pages
    participant B as MQTT broker
    participant H as Home Hub

    V->>P: GET /live/
    P-->>V: HTML + MQTT.js
    V->>B: CONNECT (wss://broker.hivemq.com:8884/mqtt)
    V->>B: SUBSCRIBE bbzorba/home-hub/v1/state and /status
    B-->>V: retained status ("online"/"offline") + last state
    loop every 10 s
        H->>B: PUBLISH state {hub, env, nodes[]}
        B-->>V: state
        V->>V: re-render cards, update "updated x s ago"
    end
    Note over V: no message for 30 s → "No update for x s"<br/>status "offline" (hub's last will) → greyed out
```

The page renders `nodes[]` generically, one card per node with whatever
sensors it reports. A new node added on the hub side (see the hub's
[README.md](https://github.com/bbzorba/ESP32C6-Zephyr-IoT-Projects/blob/main/applications/web_app/README.md), §6)
therefore shows up here without any website change.

The topic prefix `bbzorba/home-hub/v1` must match `CONFIG_APP_MQTT_TOPIC_PREFIX`
in the hub firmware.

## 4. Contact form

```mermaid
sequenceDiagram
    autonumber
    participant V as Visitor's browser
    participant F as FormSubmit
    participant M as My inbox

    V->>F: POST /ajax/bbzorba@hotmail.com {name, email, message}
    F->>M: e-mail (reply-to = visitor)
    F-->>V: {"success": "true"} → "Thank you!"
    Note over V,F: on any error the page offers a mailto: link instead
```

FormSubmit needs a one-time activation: the very first message sends a
confirmation e-mail to the inbox, and messages are delivered after the
link in it is clicked. A hidden `_honey` field filters simple spam bots.

## 5. Crucial points

- **No server of my own.** Everything dynamic runs at build time (GitHub
  Actions) or in the visitor's browser, so there is nothing to keep alive
  or patch.
- **Projects page is only as fresh as the last build.** The daily cron
  rebuild picks up new repositories.
- **Live data depends on the public broker.** The topic prefix must match
  the hub's `CONFIG_APP_MQTT_TOPIC_PREFIX`; anyone who knows it could
  publish fake values (a private broker with a read-only user fixes that).
- **The contact form needs FormSubmit's one-time activation**; until then,
  and on any error, the page falls back to a mailto: link.
