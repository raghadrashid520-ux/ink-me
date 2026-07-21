import os
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# التأكد من وجود مجلد لحفظ الصور المؤقتة
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return {"message": "Ink Me API is running successfully!"}

@app.post("/convert")
async def convert_image(file: UploadFile = File(...), enhance: str = Form("true")):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return JSONResponse(content={"status": "error", "detail": "Invalid image file"}, status_code=400)

        # تحجيم ذكي للحفاظ على الأداء ودقة التفاصيل الدقيقة للوجه
        height, width = img.shape[:2]
        max_dim = 1200
        if max(height, width) > max_dim:
            scale = max_dim / max(height, width)
            img = cv2.resize(img, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_LANCZOS4)

        output_filename = f"anime_{file.filename}"
        output_path = os.path.join("static", output_filename)

        # --- خوارزمية أنمي احترافية تحافظ على الملامح وتمنح إضاءة ورسمة متقنة ---
        
        # 1. تنقية البشرة وإبراز الملامح إذا كان الخيار مفعلاً
        if enhance == "true":
            base_img = cv2.detailEnhance(img, sigma_s=10, sigma_r=0.12)
        else:
            base_img = img

        # 2. تنعيم ذكي يحافظ على حدود وملامح الوجه الأساسية (Bilateral Filter)
        smooth = cv2.bilateralFilter(base_img, d=9, sigmaColor=75, sigmaSpace=75)

        # 3. استخراج خطوط الرسم بدقة عالية جداً (عكس مظهر الأنمي الحقيقي)
        gray = cv2.cvtColor(base_img, cv2.COLOR_BGR2GRAY)
        gray_blur = cv2.medianBlur(gray, 5)
        edges = cv2.adaptiveThreshold(gray_blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 7)
        edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

        # 4. دمج الخطوط مع الطبقة الناعمة للحصول على أساس الرسمة
        art_base = cv2.bitwise_and(smooth, edges_colored)

        # 5. معالجة الإضاءة والألوان لتصبح ساطعة وجميلة تشبه الأنمي
        hsv = cv2.cvtColor(art_base, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        
        # زيادة حيوية الألوان والتشبع بذكاء
        s = cv2.multiply(s, 1.3)
        s = np.clip(s, 0, 255).astype(np.uint8)
        
        # تحسين إضاءة الوجه (V) لتكون مشرقة وواضحة
        v = cv2.add(v, 15)
        v = np.clip(v, 0, 255).astype(np.uint8)
        
        final_hsv = cv2.merge((h, s, v))
        anime_result = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)
        
        # لمسة نهائية لزيادة عمق ووضوح الرسمة
        anime_result = cv2.convertScaleAbs(anime_result, alpha=1.12, beta=8)

        cv2.imwrite(output_path, anime_result)

        return JSONResponse(content={
            "status": "success",
            "anime_image_url": f"/static/{output_filename}"
        })

    except Exception as e:
        return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=500)
