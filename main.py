from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
import os
import cv2
import numpy as np

app = FastAPI()

# إعداد مسار القوالب للواجهة الأمامية
templates = Jinja2Templates(directory="templates")

# إنشاء مجلد لتخزين الصور المعالجة مؤقتاً
os.makedirs("static", exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """عرض صفحة الويب الرئيسية"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/convert")
async def convert_image(file: UploadFile = File(...)):
    """استلام الصورة الشخصية وتحويلها إلى شكل أنمي حقيقي مع الحفاظ التام على الملامح"""
    try:
        # قراءة محتوى الملف المرفوع وتحويله إلى مصفوفة رقمية
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # التأكد من صحة الملف وأنه صورة صالحة
        if img is None:
            return JSONResponse(
                content={"status": "error", "detail": "فشل في قراءة الصورة، يرجى التأكد من أن الملف صورة صحيحة"}, 
                status_code=400
            )

        # ضبط أبعاد الصورة لضمان دقة المعالجة والسرعة
        height, width = img.shape[:2]
        if width > 800 or height > 800:
            scaling_factor = 800 / max(width, height)
            img = cv2.resize(img, (int(width * scaling_factor), int(height * scaling_factor)), interpolation=cv2.INTER_AREA)

        # تحديد مسار وحفظ الصورة الناتجة
        output_filename = f"anime_{file.filename}"
        output_path = os.path.join("static", output_filename)

        # خوارزمية الأنمي الحقيقية (Anime Processing Pipeline):
        # 1. تقليل الألوان (Color Quantization) لإعطاء الطابع الكرتوني/المرسوم
        data = np.float32(img).reshape((-1, 3))
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 0.001)
        k = 9  # عدد مستويات الألوان لإظهار مظهر الأنمي
        _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        centers = np.uint8(centers)
        quantized = centers[labels.flatten()].reshape(img.shape)

        # 2. تنعيم البشرة والملامح بفلتر ثنائي قوي مع الحفاظ على تفاصيل الوجه الأصلية
        smooth_color = cv2.bilateralFilter(quantized, d=9, sigmaColor=150, sigmaSpace=150)

        # 3. استخراج الخطوط السوداء البارزة للأنمي (Edges) بدقة لضبط الملامح
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.medianBlur(gray, 5)
        edges = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 3)
        edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

        # 4. دمج الألوان الكرتونية النقية مع الخطوط البارزة للحصول على شكل أنمي احترافي
        anime_result = cv2.bitwise_and(smooth_color, edges_colored)

        # حفظ الصورة النهائية في مجلد static
        cv2.imwrite(output_path, anime_result)

        # إرجاع رابط النتيجة للواجهة
        return JSONResponse(content={
            "status": "success",
            "anime_image_url": f"/api/image/{output_filename}"
        })

    except Exception as e:
        return JSONResponse(
            content={"status": "error", "detail": f"حدث خطأ أثناء معالجة الصورة: {str(e)}"}, 
            status_code=500
        )

@app.get("/api/image/{image_name}")
async def get_image(image_name: str):
    """إرجاع الصورة الناتجة لعرضها وتحميلها على المتصفح"""
    image_path = os.path.join("static", image_name)
    if os.path.exists(image_path):
        return FileResponse(image_path)
    return JSONResponse(content={"error": "الصورة غير موجودة"}, status_code=404)

