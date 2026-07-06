# VS Code Setup Guide - STA Capture GUI (PySide6)

Panduan lengkap untuk setup dan debugging aplikasi PySide6 di VS Code.

---

## 📋 Prerequisites

- VS Code (terbaru)
- Python 3.8+ installed
- Project folder dibuka di VS Code

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install Extensions
```
Ctrl+Shift+X (Extensions tab)
```

Cari dan install:
1. **Python** (ms-python.python)
2. **Pylance** (ms-python.vscode-pylance) 
3. **Debugpy** (ms-python.debugpy)

Klik "Show Recommended Extensions" untuk install sekaligus.

### Step 2: Create Virtual Environment
```bash
# Di VS Code terminal (Ctrl+`)
python3 -m venv venv

# Activate (Windows):
.\venv\Scripts\Activate

# Activate (macOS/Linux):
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Run Application
```
F5  (Start Debugging)
```

atau klik Run button di atas `main()` function.

---

## 🎯 VS Code Configuration Files

Project sudah include `.vscode/` folder dengan 3 file penting:

### 1. `.vscode/launch.json`
**Apa**: Debug dan run configurations  
**Cara pakai**:
- F5 untuk start debugging dengan config pertama
- Ctrl+Shift+D untuk select run configuration lain
- Breakpoint: click left dari line number

```json
{
    "configurations": [
        {
            "name": "Python: STA Capture GUI",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/sta_capture_gui_pyside6.py",
            "console": "integratedTerminal"
        }
    ]
}
```

### 2. `.vscode/settings.json`
**Apa**: VS Code settings untuk Python development  
**Auto-apply** pada open folder

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "[python]": {
        "editor.formatOnSave": false
    }
}
```

### 3. `.vscode/extensions.json`
**Apa**: Rekomendasi extensions  
**Notification**: VS Code akan suggest untuk install saat open folder

---

## ▶️ Running Application

### Method 1: Debugging (F5) - Recommended
```
1. Open sta_capture_gui_pyside6.py
2. Press F5
3. Select "Python: STA Capture GUI"
4. Application start di integrated terminal
```

**Advantages:**
- ✓ Breakpoints & step through code
- ✓ Debug console output
- ✓ Variable inspection
- ✓ Easy stop/restart

### Method 2: Run Without Debugging (Ctrl+F5)
```
1. Open sta_capture_gui_pyside6.py
2. Press Ctrl+F5
```

**Advantages:**
- ✓ Faster startup (no debug overhead)
- ✓ Still see output in terminal

### Method 3: Terminal Command
```bash
python sta_capture_gui_pyside6.py
```

**Advantages:**
- ✓ Simple
- ✓ No IDE overhead
- ✓ Easy to pass arguments

---

## 🐛 Debugging Features

### Breakpoints
```
Click left dari line number untuk set breakpoint
Red dot = breakpoint active
Akan stop di line saat execution
```

### Step Controls
| Shortcut | Action |
|----------|--------|
| **F5** | Continue/Start |
| **F6** | Pause |
| **F10** | Step Over (execute current line) |
| **F11** | Step Into (go inside function) |
| **Shift+F11** | Step Out (exit current function) |
| **Shift+F5** | Stop Debugging |

### Debug Panel
```
Ctrl+Shift+D (Debug panel)
```

**Sections:**
1. **Variables**: Local & global variables saat breakpoint
2. **Watch**: Custom expressions untuk monitor
3. **Call Stack**: Function call hierarchy
4. **Breakpoints**: List semua breakpoints

### Debug Console
```
Bottom terminal saat debugging
```

Bisa:
- ✓ Print values: `print(variable_name)`
- ✓ Execute code: `len(list_var)`
- ✓ Access any variable dalam scope

---

## 📊 Example Debugging Session

### Scenario: Bug saat ROI selection tidak terupdate

**Step-by-step:**

1. **Find the function**
   - Open `sta_capture_gui_pyside6.py`
   - Find `_on_roi_changed` method (Ctrl+F)

2. **Set breakpoint**
   - Click line nomor 495 (di dalam function)
   - Red dot appears

3. **Run with debugging**
   - F5
   - Application start
   - GUI terbuka

4. **Trigger condition**
   - Di GUI, ubah ROI spinbox
   - Execution akan pause di breakpoint

5. **Inspect variables**
   - Debug Panel → Variables
   - Hover variable untuk lihat value
   - Or type di Debug Console: `x` → Enter

6. **Step through code**
   - F10 untuk lanjut line demi line
   - Lihat variable change di Debug Panel

7. **Fix bug**
   - Stop debugging (Shift+F5)
   - Edit kode
   - Run lagi (F5)

---

## 🎨 Editor Tips

### Code Navigation
| Shortcut | Action |
|----------|--------|
| Ctrl+P | Quick open file |
| Ctrl+G | Go to line |
| Ctrl+F | Find in file |
| Ctrl+H | Find & Replace |
| F12 | Go to definition |
| Shift+F12 | Find all references |

### Code Editing
| Shortcut | Action |
|----------|--------|
| Ctrl+/ | Toggle comment |
| Alt+↑ / Alt+↓ | Move line up/down |
| Ctrl+D | Select word (multi-select) |
| Ctrl+Shift+I | Format document |
| Ctrl+. | Quick fix / Code actions |

### Terminal
| Shortcut | Action |
|----------|--------|
| Ctrl+` | Toggle integrated terminal |
| Ctrl+Shift+` | New terminal |
| Ctrl+Shift+C | Copy terminal |
| Ctrl+Shift+X | Clear terminal |

---

## 🔍 Python Intellisense (Pylance)

### Auto-completion
- Start typing → suggestions appear
- Tab/Enter untuk pilih
- Ctrl+Space untuk manual trigger

### Hover Information
```
Hover mouse over:
- Function → signature & docstring
- Variable → type information
- Import → file path
```

### Parameter Hints
```
Inside function call
Ctrl+Shift+Space untuk show parameters
```

### Go to Definition
```
Ctrl+Click pada function/class
Atau F12
```

---

## 📦 Package Management in VS Code

### Install Package
```bash
# Di integrated terminal (Ctrl+`)
pip install package_name

# VS Code akan auto-detect di Python files
```

### View Installed Packages
```bash
pip list
```

### Upgrade Packages
```bash
pip install --upgrade PySide6
pip install --upgrade -r requirements.txt
```

### Create requirements from current env
```bash
pip freeze > requirements.txt
```

---

## ⚡ Performance Tips

### Reduce Pylance overhead
```json
// .vscode/settings.json
"python.analysis.typeCheckingMode": "basic"
```

### Faster Debugging
- Use Ctrl+F5 (Run without debugging) untuk testing
- F5 hanya untuk actual bug hunting

### Disable unused features
```json
"python.linting.pylintEnabled": false,
"python.formatting.provider": null
```

---

## 🆘 Common Issues & Solutions

### Issue: "Python extension not found"
**Solution:**
- Install Python extension (ms-python.python)
- Reload VS Code (Ctrl+R)

### Issue: "PySide6 not recognized"
**Solution:**
```bash
# Terminal: pip install PySide6
# Or reinstall from requirements
pip install -r requirements.txt
```

### Issue: Pylance errors on import
**Solution:**
1. Ctrl+Shift+P → "Python: Clear Cache"
2. Reload window (Ctrl+R)

### Issue: Debug console tidak appear
**Solution:**
1. Bottom panel → Debug Console tab
2. Or: Ctrl+Shift+D → Debug panel auto-opens

### Issue: Breakpoint not triggering
**Solution:**
1. Pastikan venv aktif
2. Debugpy installed: `pip install debugpy`
3. "justMyCode": true di launch.json
4. Restart debugging (Shift+F5 then F5)

### Issue: Terminal too many outputs
**Solution:**
```bash
# Clear terminal: Ctrl+Shift+X
# Or: cls (Windows) / clear (macOS/Linux)
```

---

## 📚 Useful Resources

- [VS Code Python Documentation](https://code.visualstudio.com/docs/languages/python)
- [Pylance Documentation](https://github.com/microsoft/pylance-release)
- [PySide6 Documentation](https://doc.qt.io/qtforpython-6/)
- [Python Debugging in VS Code](https://code.visualstudio.com/docs/python/debugging)

---

## ✅ Checklist - First Time Setup

- [ ] VS Code installed
- [ ] Python 3.8+ installed
- [ ] Project folder opened (`code .`)
- [ ] Extensions installed (Python, Pylance)
- [ ] Virtual environment created (`python3 -m venv venv`)
- [ ] venv activated
- [ ] Requirements installed (`pip install -r requirements.txt`)
- [ ] Python interpreter selected (should auto-detect venv)
- [ ] F5 works untuk launch application
- [ ] Breakpoints dapat di-set
- [ ] Debug console visible saat running

---

**Ready to debug!** 🎉

Press **F5** untuk start.

