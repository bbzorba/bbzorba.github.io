from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import httpx
import os

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Load CV and blog data
with open("data/cv_data.json", "r", encoding="utf-8") as f:
    cv_data = json.load(f)

with open("data/blog_posts.json", "r", encoding="utf-8") as f:
    blog_posts = json.load(f)

@app.get("/")
def homepage(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/resume")
def resume(request: Request):
    return templates.TemplateResponse("profile.html", {
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

@app.get("/blog")
def blog(request: Request):
    return templates.TemplateResponse("blog.html", {"request": request, "posts": blog_posts})

@app.get("/academia")
def academia(request: Request):
    with open("data/academic_works.json", "r", encoding="utf-8") as f:
        academic_works = json.load(f)
    return templates.TemplateResponse("academia.html", {"request": request, "academic_works": academic_works})

@app.get("/github")
async def github(request: Request):
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.github.com/users/bbzorba/repos")
        repos = response.json()
    return templates.TemplateResponse("github.html", {"request": request, "repos": repos})

@app.get("/embedded_world")
async def embedded_world(request: Request):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("https://api.github.com/users/bbzorba/repos")
            response.raise_for_status()  # Raise an exception for HTTP errors
            repos = response.json()
        except httpx.HTTPStatusError as e:
            return templates.TemplateResponse("error.html", {"request": request, "message": f"GitHub API error: {e}"})
        except Exception as e:
            return templates.TemplateResponse("error.html", {"request": request, "message": f"Unexpected error: {e}"})
    return templates.TemplateResponse("embedded_world.html", {"request": request, "repos": repos})

@app.get("/sports")
def sports(request: Request):
    return templates.TemplateResponse("sports.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))  # Default to 8000 if PORT is not set
    uvicorn.run("main:app", host="0.0.0.0", port=port)