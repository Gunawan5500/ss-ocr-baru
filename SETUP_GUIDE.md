# STA Screenshot Capture GUI - Setup Guide (PySide6 + VS Code)

## 📋 Requirements

### System Dependencies
- **Python 3.8+** (3.10+ recommended)
- **Tesseract-OCR** (must be installed separately)
- **FFmpeg** (untuk video processing, optional but recommended)
- **VS Code** (for development & debugging)

### Python Packages
```
PySide6>=6.4.0
opencv-python>=4.5.0
pytesseract>=0.3.8
numpy>=1.19.0
```

### VS Code Extensions (Recommended)
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Debugpy (ms-python.debugpy)

---

## 🚀 Installation

### 0. Setup VS Code (Optional but Recommended)

#### Install VS Code Extensions
1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X / Cmd+Shift+X)
3. Search and install:
   - **Python** (ms-python.python)
   - **Pylance** (ms-python.vscode-pylance)
   - **Debugpy** (for debugging)

#### VS Code Configuration
```bash
# .vscode folder already included in project
# Contains:
# - launch.json       (debug configurations)
# - settings.json     (Python development settings)
# - extensions.json   (recommended extensions)
```

Configurations sudah siap - VS Code akan auto-detect Python interpreter.

### 1. Install Tesseract OCR

**Windows:**
- Download installer dari: https://github.com/UB-Mannheim/tesseract/wiki
- Run `tesseract-ocr-w64-setup-v5.x.x.exe`
- Ingat path instalasi (default: `C:\Program Files\Tesseract-OCR`)

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install tesseract
```

---

### 2. Install Python Dependencies

#### Using VS Code Terminal (Recommended)
```bash
# Open VS Code in project folder
code .

# Open integrated terminal: Ctrl+` (backtick)

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Windows PowerShell:
.\venv\Scripts\Activate

# On Windows CMD:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

#### Using Regular Terminal
```bash
cd sta_capture_gui

# Create virtual environment
python3 -m venv venv

# Activate & install (see commands above based on OS)
```

**Note:** VS Code akan auto-detect `venv` folder dan suggest menggunakannya sebagai default interpreter.

---

### 3. Configure Tesseract Path (if needed)

Jika Tesseract tidak terdeteksi otomatis, edit `sta_capture_gui.py`:

Cari baris:
```python
# Tambahkan di bagian atas file main(), sebelum ProcessWorker:
import pytesseract
pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

Sesuaikan path dengan lokasi instalasi Tesseract Anda.

---

## 📱 Usage

### Run GUI - Method 1: VS Code (Recommended)

#### Option A: Using Debug Configuration
1. Open `sta_capture_gui_pyside6.py`
2. Press **F5** or click Run → Start Debugging
3. Select "Python: STA Capture GUI" from dropdown
4. Application akan run di integrated terminal dengan full debugging support

#### Option B: Using Run Configuration
1. Open `sta_capture_gui_pyside6.py`
2. Click "Run" button di atas main() function
3. Or: Right-click editor → "Run Python File in Terminal"

#### Option C: Terminal Command
```bash
# Di VS Code integrated terminal (Ctrl+`)
python sta_capture_gui_pyside6.py
```

### Run GUI - Method 2: Command Line
```bash
# Pastikan venv sudah active
python sta_capture_gui_pyside6.py
```

### Debug Tips (VS Code)
- **Breakpoints**: Click left dari line number untuk set breakpoint
- **Step Over**: F10
- **Step Into**: F11
- **Continue**: F5
- **Stop**: Shift+F5
- **Debug Console**: Lihat output & error messages

### Workflow Penggunaan:

#### **Tab 1: Video & ROI** 📹
1. **Select Video**
   - Klik "Browse..." dan pilih video file
   - Preview akan menampilkan frame pertama

2. **Define STA Text Region**
   - Lihat di preview di mana teks "STA" berada
   - Input koordinat pixel (X, Y, Width, Height)
   - Contoh: X=10, Y=310, Width=220, Height=40
   - ROI akan ditandai dengan kotak oranye di preview

3. **Live OCR Preview**
   - Geser slider atau play video
   - Lihat hasil OCR real-time (teks yang terdeteksi)
   - Pastikan teks STA terbaca dengan benar

#### **Tab 2: Settings** ⚙️
- **Capture Interval**: Jarak antar capture (default 100m)
  - Misal: 50m = capture setiap naik 50 meter
  - 100m = capture setiap naik 100 meter
  
- **Frame Skip**: Proses tiap N frame
  - Nilai tinggi = lebih cepat, tapi mungkin ada yang terlewat
  - Default 5 = cukup seimbang
  
- **Output Folder**: Folder penyimpanan screenshot
  - Default: `~/STA_Output`

#### **Tab 3: Process** ▶️
1. Verifikasi settings di tab sebelumnya
2. Klik **"▶ Start Processing"**
3. Lihat:
   - Progress bar (persentase selesai)
   - Log real-time (screenshot yang tersimpan)
   - OCR success rate
4. Tunggu sampai selesai atau klik **"⏹ Stop"** untuk berhenti

---

## 📊 Output

Hasil screenshot akan disimpan dengan naming:
```
STA_0+100.jpg
STA_0+200.jpg
STA_1+050.jpg   (1 km + 50 meter)
STA_12+300.jpg  (12 km + 300 meter)
```

Setiap file berisi frame video pada posisi STA tertentu.

---

## 🎨 GUI Features

### Video Preview Section
- **Play/Pause**: Control playback
- **Frame Slider**: Jump ke frame tertentu
- **Frame Counter**: Menunjukkan frame saat ini / total

### Live OCR Display
- Menampilkan teks yang terdeteksi dari ROI
- Update real-time saat geser/play video
- Warna oranye = OCR detected text

### Processing Log
- Real-time update status
- Menunjukkan filename dan text yang terdeteksi
- ✓ = sukses tersimpan
- ✗ = error atau validation failed

### Statistics
- **Screenshots Saved**: Jumlah capture berhasil
- **OCR Attempts**: Berapa banyak ROI dibaca
- **OCR Success**: Berapa yang terdeteksi teks STA-nya
- **OCR Accuracy**: Persentase keberhasilan

---

## 🎨 VS Code Tips & Tricks

### Auto-format Code
```
Ctrl+Shift+I (Windows/Linux)
Cmd+Shift+I (macOS)
```
Will format code sesuai PEP 8 standards.

### Quick Fix Issues
- **Red squiggly lines**: Hover over untuk lihat suggestions
- **Import errors**: Right-click → "Quick Fix" atau Ctrl+.
- **Undefined names**: Pylance akan suggest variable names

### Terminal
```
Ctrl+`  = Toggle integrated terminal
Ctrl+Shift+`  = New terminal
```

### Keyboard Shortcuts (Useful)
| Shortcut | Action |
|----------|--------|
| Ctrl+F | Find in file |
| Ctrl+H | Find & Replace |
| Ctrl+G | Go to line |
| Ctrl+D | Multi-select word |
| Alt+↑/↓ | Move line up/down |
| Ctrl+/ | Toggle comment |

### Settings
- Ctrl+, = Open Settings
- Sudah dikonfigurasi di `.vscode/settings.json`
- Auto-format, linting, dan debugging sudah ready

---

## 🔧 Troubleshooting

### VS Code Specific Issues

### Problem: "ModuleNotFoundError: No module named 'PySide6'"
**Solution:**
1. Pastikan venv sudah active (`source venv/bin/activate` or `.\venv\Scripts\Activate`)
2. Run `pip install PySide6`
3. Check di VS Code Terminal bahwa pip install berhasil
4. F5 untuk restart debugging

### Problem: VS Code doesn't recognize Python interpreter
**Solution:**
1. Ctrl+Shift+P → "Python: Select Interpreter"
2. Choose venv dari list (biasanya `./venv/bin/python`)
3. Atau manual set di `.vscode/settings.json`:
   ```json
   "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python"
   ```
4. Reload VS Code (Ctrl+R)

### Problem: Debugger not stopping at breakpoints
**Solution:**
1. Install extension "Debugpy": `pip install debugpy`
2. F5 untuk restart debugging
3. Pastikan "justMyCode": true di launch.json

### Problem: "Tesseract not found"
**Solution:**
1. Install Tesseract OCR (lihat bagian Installation)
2. Set path manual di kode (lihat Configure Tesseract Path)

### Problem: OCR tidak bisa baca teks
**Solution:**
1. Pastikan ROI tepat mengelilingi teks STA
2. Coba putar video dan lihat di frame lain
3. Increase frame-skip untuk sampling lebih banyak
4. Tentukan interval yang lebih besar (misalkan dari 100m jadi 200m)

### Problem: GUI sangat lambat saat preview
**Solution:**
1. Increase Frame Skip value (misal 5 → 10)
2. Gunakan video dengan resolusi lebih rendah untuk testing
3. Close aplikasi lain yang heavy

### Problem: Output folder error
**Solution:**
1. Pastikan folder path valid
2. Check write permission untuk folder tersebut
3. Avoid special characters di path folder

---

## 📝 Tips & Tricks

### Optimal ROI Selection
```
1. Play video sampai jelas terlihat text STA
2. Zoom gambar mental, lihat boundary teks
3. Beri padding sedikit di sekeliling teks
4. Jangan overlapping dengan elemen lain
```

### Better OCR Accuracy
- ROI harus **minimal 150x30 pixel** (sebelum scaling 3x)
- Text harus **high contrast** (terang/gelap jelas)
- Avoid shadows/reflections pada teks
- Coba capture dari frame berbeda jika ada motion blur

### Performance Tuning
- **Frame Skip 1**: Akurat tapi lambat
- **Frame Skip 5**: Balanced (recommended)
- **Frame Skip 10+**: Cepat tapi mungkin terlewat capture

### Interval Selection
```
100m  = Standard road survey
50m   = Detail survey / steep road
200m  = Fast overview / long road
```

---

## 📦 File Structure

```
sta_capture/
├── sta_capture_gui.py          # Main GUI application
├── sta_capture.py              # Original CLI tool
├── requirements.txt            # Python dependencies
├── SETUP_GUIDE.md             # This file
└── output/                     # Default output folder
```

---

## 🤝 Support

Untuk error atau pertanyaan:
1. Check log output di GUI tab "Process"
2. Verifikasi video format (MP4/AVI/MOV/MKV)
3. Ensure ROI visible dalam frame
4. Test dengan video berbeda untuk isolate issue

---

**Version**: 1.0  
**Last Updated**: 2024
