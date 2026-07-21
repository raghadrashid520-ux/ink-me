import os
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# إنشاء مجلد للصور المؤقتة
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return HTMLResponse(content="<h1>Welcome to Ink me - index.html not found</h1>", status_code=404)

@app.post("/convert")
async def convert_image(file: UploadFile = File(...), enhance: str = Form("true")):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return JSONResponse(content={"status": "error", "detail": "Invalid image file"}, status_code=400)

        height, width = img.shape[:2]
        max_dim = 1200
        if max(height, width) > max_dim:
            scale = max_dim / max(height, width)
            img = cv2.resize(img, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_LANCZOS4)

        output_filename = f"anime_{file.filename}"
        output_path = os.path.join("static", output_filename)

        if enhance == "true":
            base_img = cv2.detailEnhance(img, sigma_s=10, sigma_r=0.12)
        else:
            base_img = img

        smooth = cv2.bilateralFilter(base_img, d=9, sigmaColor=75, sigmaSpace=75)
        
        gray = cv2.cvtColor(base_img, cv2.COLOR_BGR2GRAY)
        gray_blur = cv2.medianBlur(gray, 5)
        edges = cv2.adaptiveThreshold(gray_blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 7)
        edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

        art_base = cv2.bitwise_and(smooth, edges_colored)

        hsv = cv2.cvtColor(art_base, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        s = cv2.multiply(s, 1.3)
        s = np.clip(s, 0, 255).astype(np.uint8)
        v = cv2.add(v, 15)
        v = np.clip(v, 0, 255).astype(np.uint8)
        
        final_hsv = cv2.merge((h, s, v))
        anime_result = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)
        anime_result = cv2.convertScaleAbs(anime_result, alpha=1.12, beta=8)

        cv2.imwrite(output_path, anime_result)

        return JSONResponse(content={
            "status": "success",
            "anime_image_url": f"/static/{output_filename}"
        })

    except Exception as e:
        return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=500)
