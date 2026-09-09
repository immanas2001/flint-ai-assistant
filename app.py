from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database.database import create_tables

from routes.chat import router as chat_router
from routes.upload import router as upload_router

# ==========================
# Create FastAPI App
# ==========================

app = FastAPI(
    title="Flint AI",
    version="1.0.0"
)

# ==========================
# Initialize Database
# ==========================

create_tables()

# ==========================
# Static Files
# ==========================

app.mount("/static", StaticFiles(directory="static"), name="static")

# ==========================
# Templates
# ==========================

templates = Jinja2Templates(directory="templates")

# ==========================
# Home Page
# ==========================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request
        }
    )

# ==========================
# Register Routes
# ==========================

app.include_router(chat_router)
app.include_router(upload_router)