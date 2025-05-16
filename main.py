from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
import json
import httpx
import os
import smtplib
from email.message import EmailMessage
import uvicorn

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Load CV and blog data
with open("data/cv_data.json", "r", encoding="utf-8") as f:
    cv_data = json.load(f)

@app.get("/")
def homepage(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/resume")
def resume(request: Request):
    with open("data/cv_data.json", "r", encoding="utf-8") as f:
        academic_works = json.load(f)
    return templates.TemplateResponse("resume.html", {
        "request": request,
        "experiences": cv_data.get("Experience", []),
        "education": cv_data.get("Education", []),
        "skills": {
            "Programming": cv_data.get("Programming Skills", []),
            "Tools": cv_data.get("Tools", []),
            "Languages": cv_data.get("Languages", [])
        },
        "certificates": cv_data.get("Certificates", []),
        "projects": cv_data.get("Projects", []),
        "areas_of_interest": cv_data.get("Areas of Interest", {}),
        "journal_papers": cv_data.get("Journal Papers", []),
        "conference_proceedings": cv_data.get("Conference Proceedings", [])
    })


@app.get("/travel_blog")
async def travel_blog(request: Request):
    with open("data/blog_posts.json", encoding="utf-8") as f:
        posts = json.load(f)
    # Ensure all keys exist and are lists
    posts.setdefault("lived", [])
    posts.setdefault("visited", [])
    posts.setdefault("want_to_go", [])
    return templates.TemplateResponse(
        "blog.html",
        {
            "request": request,
            "posts": posts
        }
    )

@app.get("/contact")
async def contact_get(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request, "sent": False, "error": None})

@app.post("/contact")
async def contact_post(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...)
):
    sent = False
    error = None

    if not name or not email or not message:
        error = "Please fill in all fields."
    else:
        try:
            # Email configuration
            smtp_server = "smtp-mail.outlook.com"
            smtp_port = 587
            smtp_user = "bbzorba@hotmail.com"  # Your email address
            smtp_password = os.environ.get("MAIL_PASSWORD")  # Set this env variable for security

            msg = EmailMessage()
            msg.set_content(
                f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}",
                "plain",
                "utf-8"
            )
            msg["Subject"] = "Contact Form Message from Website"
            msg["From"] = smtp_user
            msg["To"] = smtp_user

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)

            sent = True
            error = None
        except Exception as e:
            error = "Failed to send message. Please try again later."

    return templates.TemplateResponse(
        "contact.html",
        {
            "request": request,
            "sent": sent,
            "error": error
        }
    )

@app.get("/github")
async def github(request: Request):
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.github.com/users/bbzorba/repos")
        repos = response.json()
    return templates.TemplateResponse("github.html", {"request": request, "repos": repos})

@app.get("/my_projects")
async def my_projects(request: Request):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("https://api.github.com/users/bbzorba/repos")
            response.raise_for_status()
            repos = response.json()
        except httpx.HTTPStatusError as e:
            return templates.TemplateResponse("error.html", {"request": request, "message": f"GitHub API error: {e}"})
        except Exception as e:
            return templates.TemplateResponse("error.html", {"request": request, "message": f"Unexpected error: {e}"})
    return templates.TemplateResponse("my_projects.html", {"request": request, "repos": repos})

@app.get("/sports")
def sports(request: Request):
    return templates.TemplateResponse("sports.html", {"request": request})

@app.get("/sports/fenerbahce", response_class=HTMLResponse)
async def fenerbahce(request: Request):
    return templates.TemplateResponse("fenerbahce.html", {"request": request})

@app.get("/sports/fenerbahce_beko", response_class=HTMLResponse)
async def fenerbahce_beko(request: Request):
    return templates.TemplateResponse("fenerbahce_beko.html", {"request": request})

@app.get("/sports/fcbayern", response_class=HTMLResponse)
async def fcbayern(request: Request):
    return templates.TemplateResponse("fcbayern.html", {"request": request})

@app.get("/sports/fcbayern_basketball", response_class=HTMLResponse)
async def fcbayern_basketball(request: Request):
    return templates.TemplateResponse("fcbayern_basketball.html", {"request": request})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)