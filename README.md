# 🎥 STA Screenshot Capture GUI

**Aplikasi Desktop modern untuk menangkap screenshot otomatis dari video berdasarkan overlay Stationing (STA).**

**Built with:** PySide6 | **Development:** VS Code | **Documentation:** Complete

Sempurna untuk survei jalan/proyek konstruksi yang membutuhkan dokumentasi visual per interval jarak.

---

## ✨ Features

✅ **Live Video Preview** dengan frame-by-frame control  
✅ **Interactive ROI Selection** untuk menentukan area teks STA  
✅ **Real-time OCR Preview** menampilkan teks terdeteksi  
✅ **Automatic Screenshot Capture** per interval jarak (default 100m)  
✅ **Multi-threaded Processing** tidak freeze UI saat capturing  
✅ **Detailed Logging** dan statistik OCR accuracy  
✅ **Modern Dark Theme** dengan accent oranye  
✅ **Cross-platform** (Windows, macOS, Linux)  

---

## 🎯 Use Cases

- 📍 **Road Survey Documentation**: Capture jalan dari km 0 + 100, 0 + 200, dst
- 🏗️ **Construction Project**: Monitor progress dengan visual intervals
- 📊 **Data Collection**: Automatic photo archive berdasarkan jarak
- 🚗 **Route Documentation**: Capture scenic/hazardous points per station

---

## 📸 Screenshots

```
┌─────────────────────────────────────────────────┐
│  STA Screenshot Capture - Main Window           │
├──────────────────┬──────────────────────────────┤
│                  │  📹 Video & ROI (Tab)        │
│  Video Preview   │                              │
│  [▶ ▰▰▰▰▰▰▰ ⏭]  │  Select Video: [Browse...]  │
│                  │                              │
│  Frame 145/1200  │  Define STA Region (ROI):    │
│                  │  X: [10] Y: [310]            │
│                  │  Width: [220] Height: [40]   │
│                  │                              │
│                  │  Live OCR Preview:           │
│                  │  ╔════════════════════╗      │
│                  │  ║ STA 12+300       ║      │
│                  │  ╚════════════════════╝      │
└──────────────────┴──────────────────────────────┘
```

---

## 🚀 Quick Start

### 0️⃣ Prerequisites
- Python 3.8+
- Tesseract OCR installed
- VS Code (recommended)

### 1️⃣ Setup Environment
```bash
# Open folder di VS Code
code .

# Terminal: Create & activate venv
python3 -m venv venv

# Windows PowerShell:
.\venv\Scripts\Activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2️⃣ Run Application
```bash
# Option A: Debug mode (F5 in VS Code)
# - Full debugging & breakpoints
# - See output in integrated terminal

# Option B: Run terminal command
python sta_capture_gui_pyside6.py
```

### 3️⃣ Simple Workflow
1. **Open video** → Browse dan pilih file MP4/AVI/MOV/MKV
2. **Define ROI** → Input X, Y, Width, Height dari area teks STA
3. **Check preview** → Play video dan verifikasi OCR terbaca benar
4. **Process** → Klik "Start Processing" dan tunggu selesai

---

## 📖 Detailed Documentation

**[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Complete installation & usage:
- 🔧 Instalasi lengkap per OS (Windows, macOS, Linux)
- 🎯 Tesseract OCR setup
- 📋 Parameter explanations
- 🎨 Feature walkthrough
- 🔍 Troubleshooting

**[VSCODE_SETUP_GUIDE.md](VSCODE_SETUP_GUIDE.md)** - VS Code development setup:
- ⚡ Quick start debugging (F5)
- 🐛 Breakpoints & step through code
- 📊 Debug console & variable inspection
- ⌨️ Keyboard shortcuts & tips
- 🆘 Common issues & solutions

---

## 📁 Project Files

```
sta_capture_gui/
├── sta_capture_gui.py       ⭐ Main application
├── sta_capture.py           (Original CLI tool)
├── requirements.txt         (Python dependencies)
├── README.md               (This file)
├── SETUP_GUIDE.md          (Installation & usage guide)
└── output/                 (Default screenshot folder)
```

---

## 🎛️ GUI Components

### **Tab 1: Video & ROI** 📹
Define video input dan capture region
- Select video file
- Set ROI coordinates (pixel position)
- Live OCR preview dari selected region

### **Tab 2: Settings** ⚙️
Configure processing parameters
- **Interval**: Jarak antar capture (100m, 50m, 200m, dll)
- **Frame Skip**: Proses tiap N frame (1=detail, 5=balanced, 10+=fast)
- **Output Folder**: Lokasi penyimpanan screenshot

### **Tab 3: Process** ▶️
Jalankan dan monitor processing
- Progress bar real-time
- Live log output
- OCR success statistics

---

## 💾 Output Format

Screenshots tersimpan dengan format naming:
```
STA_{km}+{meter}.jpg

Examples:
  STA_0+100.jpg       (0 km + 100 meter)
  STA_5+500.jpg       (5 km + 500 meter)
  STA_12+300.jpg      (12 km + 300 meter)
```

Setiap file = 1 frame video pada posisi STA tertentu.

---

## 🎨 Design Highlights

- **Dark theme** untuk mata nyaman (long sessions)
- **Orange accent** (#f59e0b) untuk action buttons & OCR display
- **Monospace font** untuk technical values (authentic OCR reading)
- **Real-time feedback** video preview sync dengan log output
- **Multi-threaded** processing agar UI tidak freeze

---

## 🔧 Technical Stack

| Component | Purpose |
|-----------|---------|
| **PySide6** | Desktop GUI framework (Qt 6) |
| **OpenCV (cv2)** | Video processing & frame capture |
| **Tesseract OCR** | Text detection dari ROI |
| **Threading** | Non-blocking UI during processing |
| **VS Code** | Development environment |
| **Python 3.8+** | Language & runtime |

---

## ⚡ Performance Tips

| Setting | Speed | Accuracy |
|---------|-------|----------|
| Frame Skip 1 | Slow | ⭐⭐⭐⭐⭐ |
| Frame Skip 5 | Balanced | ⭐⭐⭐⭐ (recommended) |
| Frame Skip 10+ | Fast | ⭐⭐⭐ |

**Untuk ROI:**
- Minimal 150x30 pixel (sebelum OCR scaling)
- Hindari text yang blur/overlapping
- High contrast = better accuracy

---

## 🆘 Common Issues

| Issue | Solution |
|-------|----------|
| Tesseract not found | Install manual + set path di kode |
| OCR tidak baca teks | Check ROI tepat, coba frame lain |
| GUI lambat | Increase frame skip value |
| Output folder error | Check write permission |

**More troubleshooting:** Lihat SETUP_GUIDE.md

---

## 📊 Example Use Case

**Project**: Dokumentasi Jalan Toll Ruas A-B  
**Video**: `toll_ab_survey.mp4` (45 menit durasi)  
**ROI**: X=15, Y=305, Width=230, Height=45  
**Interval**: 100 meter  

**Hasil:**
```
✓ STA_0+100.jpg
✓ STA_0+200.jpg
✓ STA_0+300.jpg
...
✓ STA_45+900.jpg

Total: 459 screenshots captured
OCR Accuracy: 94.7%
Processing Time: ~8 minutes
```

---

## 🔐 Privacy & Security

- ✅ Semua processing **local** (tidak cloud)
- ✅ Video tidak dikirim anywhere
- ✅ Output hanya screenshot tertentu
- ✅ No external API calls

---

## 📄 License

Prototype for internal use. Modify freely.

---

## 👥 About

**Original CLI Tool:** `sta_capture.py`  
**GUI Version:** `sta_capture_gui.py` (with PyQt5 interface)

Developed untuk civil engineering survey documentation.

---

## 📞 Support

Untuk bantuan:
1. Baca **SETUP_GUIDE.md** untuk instalasi
2. Check **troubleshooting section** untuk error umum
3. Verify video format & ROI definition
4. Test dengan video sample berbeda

---

**Ready to capture?** 🎬  
`python sta_capture_gui.py`

