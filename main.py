
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
<html lang="ar" dir="rtl" id="htmlRoot">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ink me - Pro Anime Studio</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;800;900&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Cairo', sans-serif; }
        .glass-panel {
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .neon-glow {
            box-shadow: 0 0 30px rgba(236, 72, 153, 0.4), 0 0 60px rgba(168, 85, 247, 0.25);
        }
        /* ستايل شريط المقارنة قبل وبعد */
        .img-comp-container {
            position: relative;
            height: 350px;
            overflow: hidden;
            border-radius: 1rem;
        }
        .img-comp-img {
            position: absolute;
            width: 100%;
            height: 100%;
            overflow: hidden;
        }
        .img-comp-img img {
            display: block;
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .img-comp-slider {
            position: absolute;
            z-index: 9;
            cursor: ew-resize;
            width: 40px;
            height: 40px;
            background-color: #ec4899;
            border-radius: 50%;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            box-shadow: 0 0 15px rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }
        .img-comp-slider::after {
            content: "↔";
            font-size: 20px;
        }
    </style>
</head>
<body class="bg-slate-950 text-white min-h-screen flex flex-col items-center justify-between p-6 relative overflow-x-hidden">

    <!-- خلفية جمالية مضيئة -->
    <div class="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[350px] bg-gradient-to-tr from-purple-600/25 to-pink-600/30 blur-[140px] pointer-events-none rounded-full"></div>

    <!-- الهيدر -->
    <header class="w-full max-w-4xl flex justify-between items-center py-4 z-10">
        <div class="flex items-center space-x-2 space-x-reverse">
            <span class="text-2xl font-black bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">Ink me ✨</span>
        </div>
        <div class="flex items-center space-x-3 space-x-reverse">
            <button onclick="toggleLanguage()" id="langBtn" class="px-3.5 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 text-xs font-bold hover:border-pink-500 transition-all">
                English 🌐
            </button>
            <span class="text-xs px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-pink-400 hidden md:inline-block font-semibold" data-i18n="badge">الاستوديو الاحترافي</span>
        </div>
    </header>

    <!-- المحتوى الرئيسي -->
    <main class="w-full max-w-2xl my-auto z-10">
        <div class="glass-panel rounded-3xl p-8 md:p-10 shadow-2xl text-center relative">
            
            <div class="mb-8">
                <h1 class="text-4xl md:text-5xl font-black tracking-tight mb-3">
                    <span data-i18n="titlePre">استوديو تحويل</span> <span class="bg-gradient-to-r from-purple-400 via-pink-400 to-rose-400 bg-clip-text text-transparent" data-i18n="titleHighlight">الأنمي الفائق</span>
                </h1>
                <p class="text-slate-400 text-sm md:text-base" data-i18n="subtitle">فلترة ذكية للوجه، دقة سينمائية عالية، ومقارنة تفاعلية فورية</p>
            </div>

            <!-- خيارات المعالجة الإضافية -->
            <div id="optionsPanel" class="mb-6 bg-slate-900/60 p-4 rounded-2xl border border-slate-800 text-right">
                <label class="flex items-center justify-between cursor-pointer">
                    <div class="flex flex-col">
                        <span class="text-sm font-bold text-slate-200" data-i18n="optTitle">تفعيل فلترة وتنقية الوجه الذكية (HD)</span>
                        <span class="text-xs text-slate-400" data-i18n="optSub">تحسين الملامح وإزالة الشوائب لنتيجة أكثر جاذبية</span>
                    </div>
                    <input type="checkbox" id="enhanceFace" checked class="w-5 h-5 accent-pink-500 rounded cursor-pointer">
                </label>
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
                    <span class="text-sm font-semibold text-slate-200 mb-1" data-i18n="uploadText">اضغطي هنا لاختيار صورتك الشخصية</span>
                    <span class="text-xs text-slate-500" data-i18n="uploadSub">تدعم صيغ PNG, JPG بجودة عالية</span>
                    <input type="file" id="imageInput" accept="image/*" class="hidden" onchange="previewImage(event)">
                </label>
            </div>

            <!-- معاينة الصورة الأصلية -->
            <div id="previewContainer" class="hidden mb-6 animate-fadeIn">
                <div class="flex justify-between items-center mb-2 px-1">
                    <span class="text-xs font-bold text-slate-400" data-i18n="selectedImage">الصورة المحددة:</span>
                    <button onclick="resetUpload()" class="text-xs text-rose-400 hover:underline" data-i18n="changeImg">تغيير الصورة</button>
                </div>
                <div class="relative rounded-2xl overflow-hidden border border-slate-700/60 bg-slate-950 p-2 max-h-60 flex justify-center">
                    <img id="sourceImage" class="max-h-52 rounded-xl object-contain">
                </div>
                <button onclick="uploadAndConvert()" class="mt-5 w-full bg-gradient-to-r from-purple-600 via-pink-600 to-rose-600 hover:opacity-95 text-white font-bold py-4 px-6 rounded-2xl transition-all shadow-xl shadow-pink-500/25 flex items-center justify-center space-x-2 space-x-reverse text-base">
                    <span data-i18n="convertBtn">بدء التحويل الاحترافي الآن</span>
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                </button>
            </div>

            <!-- شاشة التحميل التفاعلية -->
            <div id="loading" class="hidden my-10 animate-fadeIn">
                <div class="relative w-16 h-16 mx-auto mb-4">
                    <div class="absolute inset-0 rounded-full border-4 border-pink-500/20"></div>
                    <div class="absolute inset-0 rounded-full border-4 border-pink-500 border-t-transparent animate-spin"></div>
                </div>
                <p class="text-slate-300 font-medium text-sm" data-i18n="loadingText">جاري فلترة الوجه، تحسين الملامح ورسم الأنمي بدقة...</p>
                <p class="text-xs text-slate-500 mt-1" data-i18n="loadingSub">يرجى الانتظار ثوانٍ معدودة</p>
            </div>

            <!-- النتيجة النهائية مع خاصية المقارنة (قبل وبعد) -->
            <div id="resultContainer" class="hidden mt-6 animate-fadeIn">
                <div class="flex items-center justify-between mb-3 px-1">
                    <span class="text-xs font-bold text-pink-400 uppercase tracking-wider" data-i18n="resultTitle">مقارنة ما قبل وما بعد التحويل:</span>
                </div>
                
                <!-- شريط المقارنة التفاعلي -->
                <div class="img-comp-container mb-6 border border-pink-500/40 neon-glow" id="comparisonContainer">
                    <div class="img-comp-img">
                        <img id="compAnimeImg" alt="Anime Result">
                    </div>
                    <div class="img-comp-img img-comp-overlay" id="compOriginalWrapper" style="width: 50%;">
                        <img id="compOrigImg" alt="Original Image">
                    </div>
                    <div class="img-comp-slider" id="compSlider" style="left: 50%;"></div>
                </div>

                <div class="flex gap-3">
                    <button onclick="downloadImage()" class="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3.5 px-6 rounded-2xl transition-all text-sm shadow-lg shadow-emerald-600/20 flex items-center justify-center space-x-2 space-x-reverse">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                        <span data-i18n="downloadBtn">تحميل الصورة النهائية</span>
                    </button>
                    <button onclick="resetUpload()" class="bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold py-3.5 px-5 rounded-2xl transition-all text-sm" data-i18n="anotherImg">
                        صورة أخرى
                    </button>
                </div>
            </div>

        </div>
    </main>

    <!-- الفوتر -->
    <footer class="w-full max-w-4xl text-center py-4 text-xs text-slate-500 z-10" data-i18n="footer">
        جميع الحقوق محفوظة © Ink me 2026
    </footer>

    <script>
        let currentLang = 'ar';
        let currentImageUrl = '';
        let originalBase64 = '';
        const translations = {
            ar: {
                badge: "الاستوديو الاحترافي",
                titlePre: "استوديو تحويل",
                titleHighlight: "الأنمي الفائق",
                subtitle: "فلترة ذكية للوجه، دقة سينمائية عالية، ومقارنة تفاعلية فورية",
                optTitle: "تفعيل فلترة وتنقية الوجه الذكية (HD)",
                optSub: "تحسين الملامح وإزالة الشوائب لنتيجة أكثر جاذبية",
                uploadText: "اضغطي هنا لاختيار صورتك الشخصية",
                uploadSub: "تدعم صيغ PNG, JPG بجودة عالية",
                selectedImage: "الصورة المحددة:",
                changeImg: "تغيير الصورة",
                convertBtn: "بدء التحويل الاحترافي الآن",
                loadingText: "جاري فلترة الوجه، تحسين الملامح ورسم الأنمي بدقة...",
                loadingSub: "يرجى الانتظار ثوانٍ معدودة",
                resultTitle: "مقارنة ما قبل وما بعد التحويل:",
                downloadBtn: "تحميل الصورة النهائية",
                anotherImg: "صورة أخرى",
                footer: "جميع الحقوق محفوظة © Ink me 2026",
                langButton: "English 🌐"
            },
            en: {
                badge: "Pro Studio",
                titlePre: "Super Anime",
                titleHighlight: "Conversion Studio",
                subtitle: "Smart face filtering, high cinematic resolution, and instant interactive comparison",
                optTitle: "Enable Smart Face Filtering & HD Enhancement",
                optSub: "Enhance features and clear blemishes for an attractive result",
                uploadText: "Click here to choose your personal photo",
                uploadSub: "Supports PNG, JPG formats in high quality",
                selectedImage: "Selected Image:",
                changeImg: "Change image",
                convertBtn: "Start Pro Conversion Now",
                loadingText: "Filtering face, enhancing features & drawing anime...",
                loadingSub: "Please wait a few seconds",
                resultTitle: "Before and After Comparison:",
                downloadBtn: "Download Final Image",
                anotherImg: "Another Image",
                footer: "All rights reserved © Ink me 2026",
                langButton: "العربية 🌐"
            }
        };

        function toggleLanguage() {
            currentLang = currentLang === 'ar' ? 'en' : 'ar';
            const htmlRoot = document.getElementById('htmlRoot');
            htmlRoot.setAttribute('lang', currentLang);
            htmlRoot.setAttribute('dir', currentLang === 'ar' ? 'rtl' : 'ltr');

            document.querySelectorAll('[data-i18n]').forEach(el => {
                const key = el.getAttribute('data-i18n');
                if (translations[currentLang][key]) {
                    el.textContent = translations[currentLang][key];
                }
            });
            document.getElementById('langBtn').textContent = translations[currentLang].langButton;
        }

        let selectedFile = null;

        function previewImage(event) {
            const file = event.target.files[0];
            if (file) {
                selectedFile = file;
                const reader = new FileReader();
                reader.onload = function(e) {
                    originalBase64 = e.target.result;
                    document.getElementById('sourceImage').src = originalBase64;
                    document.getElementById('dropZone').closest('.mb-6').classList.add('hidden');
                    document.getElementById('optionsPanel').classList.add('hidden');
                    document.getElementById('previewContainer').classList.remove('hidden');
                    document.getElementById('resultContainer').classList.add('hidden');
                }
                reader.readAsDataURL(file);
            }
        }

        function resetUpload() {
            selectedFile = null;
            currentImageUrl = '';
            originalBase64 = '';
            document.getElementById('imageInput').value = '';
            document.getElementById('previewContainer').classList.add('hidden');
            document.getElementById('resultContainer').classList.add('hidden');
            document.getElementById('dropZone').closest('.mb-6').classList.remove('hidden');
            document.getElementById('optionsPanel').classList.remove('hidden');
        }

        async function uploadAndConvert() {
            if (!selectedFile) return;

            document.getElementById('previewContainer').classList.add('hidden');
            document.getElementById('loading').classList.remove('hidden');

            const formData = new FormData();
            formData.append("file", selectedFile);
            const enhanceVal = document.getElementById('enhanceFace').checked;
            formData.append("enhance", enhanceVal ? "true" : "false");

            try {
                const response = await fetch("/convert", {
                    method: "POST",
                    body: formData
                });

                const result = await response.json();
                document.getElementById('loading').classList.add('hidden');

                if (result.status === "success") {
                    currentImageUrl = result.anime_image_url;
                    document.getElementById('compAnimeImg').src = currentImageUrl;
                    document.getElementById('compOrigImg').src = originalBase64;
                    document.getElementById('resultContainer').classList.remove('hidden');
                    initComparisonSlider();
                } else {
                    alert(currentLang === 'ar' ? "حدث خطأ: " + result.detail : "Error: " + result.detail);
                    document.getElementById('previewContainer').classList.remove('hidden');
                }
            } catch (error) {
                document.getElementById('loading').classList.add('hidden');
                alert(currentLang === 'ar' ? "فشل الاتصال بالسيرفر." : "Server connection failed.");
                document.getElementById('previewContainer').classList.remove('hidden');
            }
        }

        function initComparisonSlider() {
            const container = document.getElementById('comparisonContainer');
            const slider = document.getElementById('compSlider');
            const overlay = document.getElementById('compOriginalWrapper');
            
            let sliderX = 0;

            function slideReady(e) {
                e.preventDefault();
                window.addEventListener("mousemove", slideMove);
                window.addEventListener("mouseup", slideFinish);
                window.addEventListener("touchmove", slideMove);
                window.addEventListener("touchend", slideFinish);
            }

            function slideFinish() {
                window.removeEventListener("mousemove", slideMove);
                window.removeEventListener("mouseup", slideFinish);
                window.removeEventListener("touchmove", slideMove);
                window.removeEventListener("touchend", slideFinish);
            }

            function slideMove(e) {
                let pos;
                let a = container.getBoundingClientRect();
                let x = (e.pageX ? e.pageX : e.touches[0].pageX) - a.left;
                
                if (x < 0) x = 0;
                if (x > a.width) x = a.width;
                
                slide(x);
            }

            function slide(x) {
                overlay.style.width = x + "px";
                slider.style.left = x + "px";
            }

            slider.addEventListener("mousedown", slideReady);
            slider.addEventListener("touchstart", slideReady);
            
            // ضبط افتاهري للوسط
            slide(container.offsetWidth / 2);
        }

        function downloadImage() {
            if (!currentImageUrl) return;
            const a = document.createElement('a');
            a.href = currentImageUrl;
            a.download = 'ink-me-pro-anime.jpg';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return HTML_CONTENT

@app.post("/convert")
async def convert_image(file: UploadFile = File(...), enhance: str = "true"):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return JSONResponse(content={"status": "error", "detail": "Invalid image file"}, status_code=400)

        # دقة معالجة عالية جداً للحفاظ على التفاصيل الدقيقة للوجه
        height, width = img.shape[:2]
        max_dim = 1100
        if max(height, width) > max_dim:
            scale = max_dim / max(height, width)
            img = cv2.resize(img, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_LANCZOS4)

        output_filename = f"anime_{file.filename}"
        output_path = os.path.join("static", output_filename)

        # --- خوارزمية فلترة وتنقية الوجه وتحويل الأنمي الاحترافي ---
        if enhance == "true":
            # تصفية مت
