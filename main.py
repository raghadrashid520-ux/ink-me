
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

app = FastAPI()

# التأكد من وجود مجلد القوالب
os.makedirs("templates", exist_ok=True)
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """عرض واجهة المنصة الرئيسية للمستخدم"""
    return templates.TemplateResponse("index.html", {"request": request})
