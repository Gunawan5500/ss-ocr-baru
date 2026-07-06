# 📦 Project Structure

```
sta_capture_gui/
│
├── 🎯 MAIN APPLICATION
│   └── sta_capture_gui_pyside6.py          ⭐ Main GUI app (PySide6)
│
├── 📚 DOCUMENTATION
│   ├── README.md                           Overview & features
│   ├── QUICKSTART.md                       Quick run guide (START HERE!)
│   ├── SETUP_GUIDE.md                      Complete installation & usage
│   └── VSCODE_SETUP_GUIDE.md              Debugging & development in VS Code
│
├── ⚙️ CONFIGURATION
│   ├── requirements.txt                    Python dependencies (PySide6, opencv, etc)
│   ├── .gitignore                         Git ignore patterns
│   └── .vscode/                           VS Code configurations
│       ├── launch.json                    Debug configurations (F5)
│       ├── settings.json                  Python development settings
│       └── extensions.json                Recommended extensions
│
├── 📁 FOLDERS (created during use)
│   ├── venv/                              Virtual environment (auto-created)
│   └── STA_Output/                        Screenshot output folder
│
└── 📄 REFERENCE
    └── sta_capture.py                     Original CLI tool (for reference)
```

---

## 📋 File Guide

### Application
- **sta_capture_gui_pyside6.py** (⭐ START HERE)
  - Main GUI application
  - PySide6 framework
  - Full-featured with live preview, OCR, processing
  - Ready to run: `python sta_capture_gui_pyside6.py`

### Documentation (Read in Order)

1. **QUICKSTART.md** 🚀 (3 minutes)
   - Fastest way to start
   - Minimal setup instructions

2. **README.md** 📖 (10 minutes)
   - Project overview
   - Features & use cases
   - Design highlights

3. **SETUP_GUIDE.md** 🔧 (Detailed)
   - Complete installation per OS
   - Tesseract OCR setup
   - Usage walkthrough
   - Troubleshooting

4. **VSCODE_SETUP_GUIDE.md** 🐛 (For developers)
   - VS Code setup
   - Debugging tips
   - Keyboard shortcuts
   - Advanced debugging

### Configuration

- **requirements.txt**
  - All Python dependencies
  - Ready to install: `pip install -r requirements.txt`

- **.vscode/launch.json**
  - Debug configurations
  - Run with F5
  - Already configured for PySide6

- **.vscode/settings.json**
  - Python development settings
  - Auto-formatting rules
  - Already configured

- **.vscode/extensions.json**
  - Recommended extensions
  - VS Code suggests on open

---

## 🚀 Getting Started (Pick Your Path)

### Path A: Just Want to Run It? (5 min)
```
1. Read: QUICKSTART.md
2. Open terminal: code .
3. Run: pip install -r requirements.txt
4. Press: F5
```

### Path B: Complete Setup + Understanding (30 min)
```
1. Read: README.md
2. Read: SETUP_GUIDE.md (installation section)
3. Install dependencies
4. Run application
5. Read: Usage section in SETUP_GUIDE.md
```

### Path C: Developer with VS Code (45 min)
```
1. Read: QUICKSTART.md
2. Read: VSCODE_SETUP_GUIDE.md
3. Setup VS Code debugger
4. Create virtual environment
5. Install dependencies
6. Debug with F5 & breakpoints
7. Modify & experiment!
```

---

## 🎯 What Each Tool Does

| Tool | What it Does |
|------|--------------|
| **sta_capture_gui_pyside6.py** | The app itself - run this |
| **requirements.txt** | Lists packages to install |
| **.vscode/launch.json** | Tells VS Code how to run/debug |
| **README.md** | Features & overview |
| **SETUP_GUIDE.md** | Step-by-step installation |
| **VSCODE_SETUP_GUIDE.md** | Debugging tutorial |
| **QUICKSTART.md** | Super fast start guide |

---

## 💾 Installation Summary

```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate it
.\venv\Scripts\Activate              # Windows PowerShell
source venv/bin/activate             # macOS/Linux

# 3. Install packages
pip install -r requirements.txt

# 4. Run application
python sta_capture_gui_pyside6.py
# OR in VS Code: Press F5
```

---

## 🔗 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| **PySide6** | >= 6.4.0 | GUI framework (Qt 6) |
| **opencv-python** | >= 4.5.0 | Video processing |
| **pytesseract** | >= 0.3.8 | OCR (text recognition) |
| **numpy** | >= 1.19.0 | Numerical computing |

---

## ✅ Verification

### Correct Installation
```bash
# These should work without errors:
python -c "import PySide6; print('✓ PySide6')"
python -c "import cv2; print('✓ OpenCV')"
python -c "import pytesseract; print('✓ Tesseract')"
python sta_capture_gui_pyside6.py  # Should open GUI window
```

### VS Code Ready
```
Check left sidebar:
✓ Python extension installed
✓ venv folder visible
✓ Can press F5 to debug
```

---

## 🎓 Learning Resources

- **Qt/PySide6**: https://doc.qt.io/qtforpython-6/
- **OpenCV**: https://opencv.org/
- **Tesseract OCR**: https://github.com/UB-Mannheim/tesseract/wiki
- **VS Code Debugging**: https://code.visualstudio.com/docs/python/debugging

---

## 📞 Quick Reference

```bash
# Virtual environment
python3 -m venv venv        # Create
source venv/bin/activate    # Activate (macOS/Linux)
.\venv\Scripts\Activate     # Activate (Windows)

# Installation
pip install -r requirements.txt

# Running
python sta_capture_gui_pyside6.py

# VS Code
code .                      # Open folder
F5                         # Start debugging
Ctrl+Shift+P               # Command palette
```

---

**Next Step:** Read `QUICKSTART.md` for 3-minute setup! 🚀

