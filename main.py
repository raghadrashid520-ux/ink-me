from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import cv2
import numpy as np

app = FastAPI()

os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ink me - تحويل الصور إلى أنمي بدقة الملامح</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;800;900&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Cairo', sans-serif; }
        .glass-panel {
            background: rgba(15, 23, 42, 0.75);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
    </style>
</head>
<body class="bg-slate-950 text-white min-h-screen flex flex-col items-center justify-between p-6 relative overflow-x-hidden">

    <!-- خلفية جمالية مضيئة -->
    <div class="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-gradient-to-tr from-purple-600/20 to-pink-600/25 blur-[120px] pointer-events-none rounded-full"></div>

    <!-- الهيدر -->
    <header class="w-full max-w-4xl flex justify-between items-center py-4 z-10">
        <div class="flex items-center space-x-2 space-x-reverse">
            <span class="text-2xl font-black bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">Ink me ✨</span>
        </div>
        <span class="text-xs px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-slate-400">النسخة الاحترافية</span>
    </header>

    <!-- المحتوى الرئيسي -->
    <main class="w-full max-w-2xl my-auto z-10">
        <div class="glass-panel rounded-3xl p-8 md:p-10 shadow-2xl text-center relative">
            
            <div class="mb-8">
                <h1 class="text-4xl md:text-5xl font-black tracking-tight mb-3">
                    حوّلي صورتك إلى <span class="bg-gradient-to-r from-purple-400 via-pink-400 to-rose-400 bg-clip-text text-transparent">أنمي فني</span>
                </h1>
                <p class="text-slate-400 text-sm md:text-base">تقنية معالجة متطورة تحافظ على تعابير وجهك وملامحك الحقيقية بدقة عالية</p>
            </div>

            <!-- منطقة رفع الصورة -->
            <div class="mb-6">
                <label id="dropZone" class="flex flex-col items-center justify-center border-2 border-dashed border-slate-700 hover:border-pink-500/70 rounded-2xl p-8 cursor-pointer transition-all bg-slate-900/40 group relative overflow-hidden">
                    <div class="absolute inset-0 bg-gradient-to-r from-purple-500/5 to-pink-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    <div class="w-16 h-16 rounded-2xl bg-slate-800/80 flex items-center justify-center text-pink-400 mb-4 group-hover:scale-110 transition-transform shadow-inner">
                        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                        </svg>
                    </div>
                    <span class="text-sm font-semibold text-slate-200 mb-1">اضغطي هنا لاختيار صورتك الشخصية</span>
                    <span class="text-xs text-slate-500">تدعم صيغ PNG, JPG بجميع الأحجام</span>
                    <input type="file" id="imageInput" accept="image/*" class="hidden" onchange="previewImage(event)">
                </label>
            </div>

            <!-- معاينة الصورة الأصلية -->
            <div id="previewContainer" class="hidden mb-6 animate-fadeIn">
                <div class="flex justify-between items-center mb-2 px-1">
                    <span class="text-xs font-bold text-slate-400">الصورة المحددة:</span>
                    <button onclick="resetUpload()" class="text-xs text-rose-400 hover:underline">تغيير الصورة</button>
                </div>
                <div class="relative rounded-2xl overflow-hidden border border-slate-700/60 bg-slate-950 p-2 max-h-60 flex justify-center">
                    <img id="sourceImage" class="max-h-52 rounded-xl object-contain">
                </div>
                <button onclick="uploadAndConvert()" class="mt-5 w-full bg-gradient-to-r from-purple-600 via-pink-600 to-rose-600 hover:opacity-95 text-white font-bold py-4 px-6 rounded-2xl transition-all shadow-xl shadow-pink-500/25 flex items-center justify-center space-x-2 space-x-reverse text-base">
                    <span>بدء التحويل إلى أنمي الآن</span>
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                </button>
            </div>

            <!-- شاشة التحميل التفاعلية -->
            <div id="loading" class="hidden my-10 animate-fadeIn">
                <div class="relative w-16 h-16 mx-auto mb-4">
                    <div class="absolute inset-0 rounded-full border-4 border-pink-500/20"></div>
                    <div class="absolute inset-0 rounded-full border-4 border-pink-500 border-t-transparent animate-spin"></div>
                </div>
                <p class="text-slate-300 font-medium text-sm">جاري تحليل الملامح ورسم الإطارات الفنية...</p>
                <p class="text-xs text-slate-500 mt-1">قد يستغرق ذلك بضع ثوانٍ</p>
            </div>

            <!-- النتيجة النهائية -->
            <div id="resultContainer" class="hidden mt-6 animate-fadeIn">
                <div class="flex items-center justify-between mb-3 px-1">
                    <span class="text-xs font-bold text-pink-400 uppercase tracking-wider">النتيجة النهائية (أنمي):</span>
                </div>
                <div class="relative rounded-2xl overflow-hidden border border-pink-500/30 bg-slate-950 p-2 max-h-72 flex justify-center mb-6 shadow-2xl">
                    <img id="animeResultImage" class="max-h-64 rounded-xl object-contain">
                </div>
                <div class="flex gap-3">
                    <a id="downloadBtn" class="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3.5 px-6 rounded-2xl transition-all text-sm shadow-lg shadow-emerald-600/20 flex items-center justify-center space-x-2 space-x-reverse">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                        <span>تحميل الصورة</span>
                    </a>
                    <button onclick="resetUpload()" class="bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold py-3.5 px-5 rounded-2xl transition-all text-sm">
                        صورة أخرى
                    </button>
                </div>
            </div>

        </div>
    </main>

    <!-- الفوتر -->
    <footer class="w-full max-w-4xl text-center py-4 text-xs text-slate-500 z-10">
        جميع الحقوق محفوظة © Ink me 2026
    </footer>

    <script>
        let selectedFile = null;

        function previewImage(event) {
            const file = event.target.files[0];
            if (file) {
                selectedFile = file;
                const reader = new FileReader();
                reader.onload = function(e) {
                    document.getElementById('sourceImage').src = e.target.result;
                    document.getElementById('dropZone').closest('.mb-6').classList.add('hidden');
                    document.getElementById('previewContainer').classList.remove('hidden');
                    document.getElementById('resultContainer').classList.add('hidden');
                }
                reader.readAsDataURL(file);
            }
        }

        function resetUpload() {
            selectedFile = null;
            document.getElementById('imageInput').value = '';
            document.getElementById('previewContainer').classList.add('hidden');
            document.getElementById('resultContainer').classList.add('hidden');
            document.getElementById('dropZone').closest('.mb-6').classList.remove('hidden');
        }

        async function uploadAndConvert() {
            if (!selectedFile) return;

            document.getElementById('previewContainer').classList.add('hidden');
            document.getElementById('loading').classList.remove('hidden');

            const formData = new FormData();
            formData.append("file", selectedFile);

            try {
                const response = await fetch("/convert", {
                    method: "POST",
                    body: formData
                });

                const result = await response.json();
                document.getElementById('loading').classList.add('hidden');

                if (result.status === "success") {
                    document.getElementById('animeResultImage').src = result.anime_image_url;
                    document.getElementById('downloadBtn').href = result.anime_image_url;
                    document.getElementById('resultContainer').classList.remove('hidden');
                } else {
                    alert("حدث خطأ: " + result.detail);
                    document.getElementById('previewContainer').classList.remove('hidden');
                }
            } catch (error) {
                document.getElementById('loading').classList.add('hidden');
                alert("فشل الاتصال بالسيرفر.");
                document.getElementById('previewContainer').classList.remove('hidden');
            }
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return HTML_CONTENT

@app.post("/convert")
async def convert_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return JSONResponse(content={"status": "error", "detail": "الملف ليس صورة صحيحة"}, status_code=400)

        height, width = img.shape[:2]
        max_dim = 700
        if max(height, width) > max_dim:
            scale = max_dim / max(height, width)
            img = cv2.resize(img, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_AREA)

        output_filename = f"anime_{file.filename}"
        output_path = os.path.join("static", output_filename)

        # خوارزمية OpenCV لمعالجة الملامح والخطوط بدقة
        smooth = cv2.bilateralFilter(img, d=9, sigmaColor=75, sigmaSpace=75)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.medianBlur(gray, 7)
        edges = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
        edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        
        anime_result = cv2.bitwise_and(smooth, edges_colored)
        cv2.imwrite(output_path, anime_result)

        return JSONResponse(content={
            "status": "success",
            "anime_image_url": f"/static/{output_filename}"
        })

    except Exception as e:
        return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=500)

