from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import cv2
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/transform")
async def transform_image(file: UploadFile = File(...), style: str = Form(...)):
    # توليد أسماء فريدة وآمنة خالية من المسافات والأحرف الخاصة لمنع أي أخطاء
    unique_id = str(uuid.uuid4())[:8]
    temp_file_path = f"temp_{unique_id}.jpg"
    output_path = f"anime_{unique_id}.jpg"
    
    try:
        # حفظ الصورة المرفوعة بلغة وأمان تام
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # قراءة الصورة عبر OpenCV
        img = cv2.imread(temp_file_path)
        if img is None:
            raise ValueError("تعذر قراءة ملف الصورة المرفوعة، تأكد من صيغة الملف.")

        # معالجة احترافية لتحويل الصورة إلى لوحة أنمي كرتونية ناعمة وملونة
        # 1. تنعيم الحواف والبشرة
        filtered = cv2.bilateralFilter(img, d=15, sigmaColor=75, sigmaSpace=75)
        
        # 2. زيادة حيوية وتشبع الألوان لتناسب ستايل الأنمي
        hsv = cv2.cvtColor(filtered, cv2.COLOR_BGR2HSV)
        hsv[:, :, 1] = cv2.multiply(hsv[:, :, 1], 1.3)  # تشبع الألوان
        vibrant_img = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        # 3. دمج الخطوط الكرتونية الناعمة
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.medianBlur(gray, 5)
        edges = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 2)
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        
        # الدمج النهائي للأنمي
        anime_result = cv2.bitwise_and(vibrant_img, edges)

        # حفظ الصورة الناتجة
        cv2.imwrite(output_path, anime_result)

        # إرجاع رابط الصورة المعالجة للواجهة بنجاح تام
        return JSONResponse(content={
            "status": "success",
            "anime_image_url": f"http://127.0.0.1:8000/api/image/{output_path}"
        })
        
    except Exception as e:
        print(f"[ERROR Details]: {str(e)}")
        return JSONResponse(content={
            "status": "error",
            "detail": str(e)
        }, status_code=500)
        
    finally:
        # تنظيف الملف المؤقت الأصلي فقط
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/api/image/{image_name}")
async def get_image(image_name: str):
    if os.path.exists(image_name):
        return FileResponse(image_name)
    return JSONResponse(content={"error": "Image not found"}, status_code=404)