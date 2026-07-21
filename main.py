from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
import os
import cv2
import numpy as np

app = FastAPI()

# إعداد قوالب الواجهة الأمامية
templates = Jinja2Templates(directory="templates")

# التأكد من وجود مجلد static لتخزين الصور المعالجة
os.makedirs("static", exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/convert")
async def convert_image(file: UploadFile = File(...)):
    try:
        # قراءة الصورة المرفوعة وتحويلها إلى مصفوفة بايثون آمنة
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return JSONResponse(
                content={"status": "error", "detail": "الملف المرفوع ليس صورة صالحة"}, 
                status_code=400
            )

        # تحجيم الصورة لتكون خفيفة جداً على خوادم الاستضافات المجانية وتجنب أي خطأ في الذاكرة
        height, width = img.shape[:2]
        max_dim = 600
        if max(height, width) > max_dim:
            scale = max_dim / max(height, width)
            img = cv2.resize(img, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_AREA)

        # مسار حفظ الصورة الناتجة
        output_filename = f"anime_{file.filename}"
        output_path = os.path.join("static", output_filename)

        # معالجة احترافية وآمنة لإنتاج تأثير الأنمي مع الحفاظ على ملامح الوجه بدقة
        # 1. تنعيم البشرة والملامح بفلتر ثنائي خفيف ومستقر
        smooth = cv2.bilateralFilter(img, d=9, sigmaColor=75, sigmaSpace=75)
        
        # 2. استخراج الحواف السوداء للرسم الكرتوني
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.medianBlur(gray, 5)
        edges = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 2)
        edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        
        # 3. دمج الألوان الناعمة مع الحواف للحصول على مظهر الأنمي الحقيقي
        anime_result = cv2.bitwise_and(smooth, edges_colored)

        # حفظ الصورة المعالجة نهائياً
        cv2.imwrite(output_path, anime_result)

        # إرجاع رابط الصورة للواجهة الأمامية
        return JSONResponse(content={
            "status": "success",
            "anime_image_url": f"/api/image/{output_filename}"
        })

    except Exception as e:
        return JSONResponse(
            content={"status": "error", "detail": f"خطأ في المعالجة: {str(e)}"}, 
            status_code=500
        )

@app.get("/api/image/{image_name}")
async def get_image(image_name: str):
    image_path = os.path.join("static", image_name)
    if os.path.exists(image_path):
        return FileResponse(image_path)
    return JSONResponse(content={"error": "الصورة غير موجودة"}, status_code=404)

