from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
import os
import cv2
import numpy as np

app = FastAPI()

templates = Jinja2Templates(directory="templates")

os.makedirs("static", exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/convert")
async def convert_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return JSONResponse(content={"status": "error", "detail": "فشل في قراءة الصورة"}, status_code=400)

        output_filename = f"anime_{file.filename}"
        output_path = os.path.join("static", output_filename)

        filtered = cv2.bilateralFilter(img, 9, 75, 75)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.medianBlur(gray, 5)
        edges = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 2)
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        
        anime_result = cv2.bitwise_and(filtered, edges)
        cv2.imwrite(output_path, anime_result)

        return JSONResponse(content={
            "status": "success",
            "anime_image_url": f"/api/image/{output_filename}"
        })
    except Exception as e:
        return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=500)

@app.get("/api/image/{image_name}")
async def get_image(image_name: str):
    image_path = os.path.join("static", image_name)
    if os.path.exists(image_path):
        return FileResponse(image_path)
    return JSONResponse(content={"error": "Image not found"}, status_code=404)
