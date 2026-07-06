"""
GUI Desktop untuk STA Screenshot Capture - PySide6 Version
Fitur: Live video preview, interactive ROI selection, real-time OCR, processing log
Built for VS Code development environment
"""

import sys
import os
import re
from pathlib import Path
from collections import deque
import gc
import torch

import cv2
import easyocr
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QSpinBox, QDoubleSpinBox, QLineEdit, QFileDialog,
    QTabWidget, QFrame, QSlider, QComboBox, QTextEdit, QProgressBar,
    QGroupBox, QGridLayout, QCheckBox, QStatusBar, QMessageBox, QListWidget,
    QListWidgetItem, QRadioButton, QButtonGroup
)
from PySide6.QtGui import QImage, QPixmap, QFont, QColor, QPainter, QPen
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QThread, QRect

# Support both formats: "0+000" (plus) and "0.021" (dot/KM format)
# Handled in parse_sta method


class WorkerSignals(QObject):
    """Signals untuk worker thread"""
    progress = Signal(int)
    finished = Signal()
    log = Signal(str)
    stats = Signal(dict)


class ProcessWorker(QThread):
    """Worker thread untuk processing video tanpa freeze UI dengan batch processing GPU"""
    
    def __init__(self, video_path, roi, interval, output_folder, frame_skip, video_name=None, batch_size=6):
        super().__init__()
        self.signals = WorkerSignals()
        self.video_path = video_path
        self.roi = roi
        self.interval = interval
        self.output_folder = output_folder
        self.frame_skip = frame_skip
        self.video_name = video_name or Path(video_path).stem
        self.is_running = True
        
        # Detect GPU availability untuk strategy selection
        self.has_gpu = torch.cuda.is_available()
        self.batch_size = batch_size if self.has_gpu else 1  # CPU: single frame (no batch)
        
        # Initialize EasyOCR reader on GPU
        try:
            device = 'cuda' if self.has_gpu else 'cpu'
            self.reader = easyocr.Reader(['en'], gpu=self.has_gpu, model_storage_directory=None)
            self.device = device
            device_name = f"GPU ({torch.cuda.get_device_name(0)})" if self.has_gpu else "CPU"
            self.signals.log.emit(f"✅ EasyOCR initialized on {device_name}")
            
            # Strategy info
            if self.has_gpu:
                self.signals.log.emit(f"⚡ Using GPU batch processing (batch_size={batch_size})")
            else:
                self.signals.log.emit(f"💾 Using CPU single-frame processing (optimized for speed)")
        except Exception as e:
            self.signals.log.emit(f"⚠️  EasyOCR GPU initialization failed, using CPU: {str(e)}")
            self.reader = easyocr.Reader(['en'], gpu=False)
            self.device = 'cpu'
            self.has_gpu = False
            self.batch_size = 1
    
    def run(self):
        try:
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                self.signals.log.emit("❌ Gagal membuka video")
                return
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            x, y, w, h = self.roi
            
            frame_idx = 0
            last_saved_multiple = None
            last_value = None
            last_frame = None
            last_ocr_text = None
            saved_count = 0
            read_attempts = 0
            read_success = 0
            
            self.signals.log.emit(f"📹 Video: {self.video_name}")
            self.signals.log.emit(f"📹 Total frames: {total_frames}, FPS: {fps}")
            self.signals.log.emit(f"🎯 ROI: x={x}, y={y}, w={w}, h={h}")
            self.signals.log.emit(f"📏 Interval: {self.interval}m\n")
            
            # Strategy berdasarkan GPU availability
            if self.has_gpu:
                # GPU: Use batch processing
                roi_batch = deque(maxlen=self.batch_size)
                frame_batch = deque(maxlen=self.batch_size)
                frame_idx_batch = deque(maxlen=self.batch_size)
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    # Process remaining batch (GPU only)
                    if self.has_gpu and roi_batch:
                        last_value, last_saved_multiple, last_frame, last_ocr_text, saved_count, read_attempts, read_success = \
                            self._process_batch(roi_batch, frame_batch, frame_idx_batch, 
                                               last_value, last_saved_multiple, 
                                               last_frame, last_ocr_text, saved_count, read_attempts, read_success)
                    break
                
                if not self.is_running:
                    self.signals.log.emit("⏹️  Processing dihentikan oleh user")
                    break
                
                if frame_idx % self.frame_skip == 0:
                    roi_img = frame[y:y + h, x:x + w]
                    
                    if self.has_gpu:
                        # GPU: Batch processing
                        roi_batch.append(roi_img)
                        frame_batch.append(frame.copy())
                        frame_idx_batch.append(frame_idx)
                        
                        if len(roi_batch) == self.batch_size:
                            last_value, last_saved_multiple, last_frame, last_ocr_text, saved_count, read_attempts, read_success = \
                                self._process_batch(roi_batch, frame_batch, frame_idx_batch, 
                                                   last_value, last_saved_multiple, 
                                                   last_frame, last_ocr_text, saved_count, read_attempts, read_success)
                    else:
                        # CPU: Direct single-frame processing (no batch)
                        text = self.ocr_read(roi_img)
                        value = self.parse_sta(text)
                        read_attempts += 1
                        
                        if value is not None:
                            read_success += 1
                            if last_value is not None:
                                diff = value - last_value
                                if diff < -5 or diff > self.interval * 5:
                                    frame_idx += 1
                                    continue
                            last_value = value
                            last_frame = frame.copy()
                            last_ocr_text = text
                            
                            current_multiple = int(value // self.interval) * self.interval
                            if last_saved_multiple is None or current_multiple > last_saved_multiple:
                                last_saved_multiple = current_multiple
                                km = int(current_multiple // 1000)
                                m = int(current_multiple % 1000)
                                filename = f'STA_{km}+{m:03d}.jpg'
                                filepath = os.path.join(self.output_folder, filename)
                                cv2.imwrite(filepath, frame)
                                saved_count += 1
                                self.signals.log.emit(f'✓ {filename}  (OCR: "{text}")')
                
                frame_idx += 1
                progress = int(100 * frame_idx / total_frames)
                self.signals.progress.emit(progress)
            
            # Last 1 second: Find frame BEFORE blank STA appears
            self.signals.log.emit(f"\n🔍 Searching last 1 second for frame before STA blank...\n")
            
            frames_in_1_second = int(1 * fps)
            start_frame = max(0, total_frames - frames_in_1_second)
            
            self.signals.log.emit(f"  Scanning frames {start_frame} to {total_frames-1} (1 sec lookback)")
            
            last_valid_value = None
            last_valid_frame = None
            last_valid_text = None
            found_blank = False
            
            for frame_idx in range(start_frame, total_frames):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret:
                    continue
                
                roi_img = frame[y:y + h, x:x + w]
                text = self.ocr_read(roi_img)
                value = self.parse_sta(text)
                
                if value is None:
                    # Frame ini BLANK/None - artinya ketemu blank!
                    found_blank = True
                    self.signals.log.emit(f"  ✓ Found blank STA at frame {frame_idx}")
                    break
                else:
                    # Frame masih punya value - update last valid
                    last_valid_value = value
                    last_valid_frame = frame.copy()
                    last_valid_text = text
            
            # Save frame terakhir sebelum blank
            if found_blank and last_valid_frame is not None:
                km = int(last_valid_value // 1000)
                m = int(last_valid_value % 1000)
                filename = f'STA_{km}+{m:03d}.jpg'
                filepath = os.path.join(self.output_folder, filename)
                cv2.imwrite(filepath, last_valid_frame)
                saved_count += 1
                self.signals.log.emit(f'✓ {filename} (LAST BEFORE BLANK)  (OCR: "{last_valid_text}")')
            else:
                self.signals.log.emit(f"  (No blank found in last 1 second - STA stayed visible)")
            
            cap.release()
            stats = {
                'saved': saved_count,
                'attempts': read_attempts,
                'success': read_success,
                'accuracy': (100 * read_success / read_attempts) if read_attempts > 0 else 0
            }
            self.signals.stats.emit(stats)
            self.signals.finished.emit()
            
        except Exception as e:
            self.signals.log.emit(f"❌ Error: {str(e)}")
            self.signals.finished.emit()
    
    def stop(self):
        self.is_running = False
    
    def _process_batch(self, roi_batch, frame_batch, frame_idx_batch, last_value, last_saved_multiple, 
                       last_frame, last_ocr_text, saved_count, read_attempts, read_success):
        """Process batch of ROI images with EasyOCR (GPU accelerated)"""
        if not roi_batch:
            return last_value, last_saved_multiple, last_frame, last_ocr_text, saved_count, read_attempts, read_success
        
        roi_list = list(roi_batch)
        frame_list = list(frame_batch)
        
        # Batch OCR processing (GPU)
        ocr_texts = self.ocr_read_batch(roi_list)
        
        # Process results
        for ocr_text, full_frame in zip(ocr_texts, frame_list):
            value = self.parse_sta(ocr_text)
            read_attempts += 1
            
            if value is not None:
                read_success += 1
                if last_value is not None:
                    diff = value - last_value
                    if diff < -5 or diff > self.interval * 5:
                        continue
                last_value = value
                last_frame = full_frame.copy()
                last_ocr_text = ocr_text
                
                current_multiple = int(value // self.interval) * self.interval
                if last_saved_multiple is None or current_multiple > last_saved_multiple:
                    last_saved_multiple = current_multiple
                    km = int(current_multiple // 1000)
                    m = int(current_multiple % 1000)
                    filename = f'STA_{km}+{m:03d}.jpg'
                    filepath = os.path.join(self.output_folder, filename)
                    cv2.imwrite(filepath, full_frame)
                    saved_count += 1
                    self.signals.log.emit(f'✓ {filename}  (OCR: "{ocr_text}")')
        
        return last_value, last_saved_multiple, last_frame, last_ocr_text, saved_count, read_attempts, read_success
    
    @staticmethod
    def parse_sta(text):
        """Parse STA value from text - support both formats:
        Format 1: "0+000", "0+100", "1+000" (plus format) → meter value
        Format 2: "KM 0.021", "0.500" (dot/KM format) → meter value
        """
        # Try format: "0+000" or "0+100" (plus format)
        match = re.search(r'(\d{1,4})\s*\+\s*(\d{1,3}(?:\.\d{1,2})?)', text)
        if match:
            km = int(match.group(1))
            m = float(match.group(2))
            return km * 1000 + m
        
        # Try format: "KM 0.021" or "0.021" (dot format = KM value)
        match = re.search(r'(?:KM\s*)?(\d+)\.(\d+)', text)
        if match:
            km_part = int(match.group(1))
            decimal_part = match.group(2)
            # Convert KM format to meters
            # "0.021" → 0.021 * 1000 = 21m
            # "0.100" → 0.100 * 1000 = 100m
            # "1.500" → 1.500 * 1000 = 1500m
            value = float(f"{km_part}.{decimal_part}") * 1000
            return value
        
        return None
    
    @staticmethod
    def preprocess(roi_img, scale=1):
        """Preprocess untuk EasyOCR - lightweight preprocessing saja"""
        # Resize untuk better OCR accuracy
        h, w = roi_img.shape[:2]
        roi_resized = cv2.resize(roi_img, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)
        return roi_resized
    
    def ocr_read(self, img):
        """Single image OCR dengan EasyOCR"""
        try:
            results = self.reader.readtext(img, detail=0)  # detail=0 untuk hanya text
            text = ''.join(results)
            return text.strip()
        except Exception as e:
            self.signals.log.emit(f"⚠️  OCR error: {str(e)}")
            return ""
    
    def ocr_read_batch(self, img_list):
        """Batch OCR processing (GPU optimized) - multiple images at once"""
        try:
            # EasyOCR readtext dapat handle list of images (batch processing)
            batch_results = []
            for img in img_list:
                try:
                    results = self.reader.readtext(img, detail=0)
                    text = ''.join(results).strip()
                    batch_results.append(text)
                except:
                    batch_results.append("")
            
            # Clean up GPU memory setelah batch
            if self.device == 'cuda':
                torch.cuda.empty_cache()
            
            return batch_results
        except Exception as e:
            self.signals.log.emit(f"⚠️  Batch OCR error: {str(e)}")
            return [""] * len(img_list)


class VideoPreviewWidget(QFrame):
    """Widget untuk display preview video dengan ROI selection"""
    roi_drawn = Signal(tuple)  # Emit (x, y, w, h) saat user selesai draw ROI
    
    def __init__(self):
        super().__init__()
        self.label = QLabel()
        self.label.setStyleSheet("background-color: #0a0a0a; border: 2px solid #1e3a5f;")
        self.label.setMinimumSize(640, 480)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        self.roi_rect = None
        self.mouse_down = False
        self.start_point = None
        self.is_drawing = False
        self.scale_factor = 1.0  # Untuk konversi koordinat preview ke video asli
        self.label.mousePressEvent = self._on_mouse_press
        self.label.mouseMoveEvent = self._on_mouse_move
        self.label.mouseReleaseEvent = self._on_mouse_release
    
    def set_pixmap(self, pixmap, roi=None, scale_factor=1.0):
        """Set pixmap dengan optional ROI rectangle. Scale factor untuk konversi koordinat."""
        self.scale_factor = scale_factor
        if roi:
            painter = QPainter(pixmap)
            painter.setPen(QPen(QColor("#f59e0b"), 3, Qt.PenStyle.SolidLine))
            x, y, w, h = roi
            # Gambar ROI dengan scaled coordinates (preview coords)
            scaled_x = int(x * scale_factor)
            scaled_y = int(y * scale_factor)
            scaled_w = int(w * scale_factor)
            scaled_h = int(h * scale_factor)
            painter.drawRect(scaled_x, scaled_y, scaled_w, scaled_h)
            painter.end()
        self.label.setPixmap(pixmap)
    
    def _on_mouse_press(self, event):
        if self.is_drawing:
            self.start_point = event.pos()
            self.mouse_down = True
    
    def _on_mouse_move(self, event):
        if self.is_drawing and self.mouse_down and self.start_point:
            self.roi_rect = QRect(self.start_point, event.pos())
    
    def _on_mouse_release(self, event):
        if self.is_drawing and self.mouse_down:
            self.mouse_down = False
            if self.roi_rect:
                # Konversi ROI dari scaled preview coords ke original video coords
                x = int(self.roi_rect.left() / self.scale_factor)
                y = int(self.roi_rect.top() / self.scale_factor)
                w = int(self.roi_rect.width() / self.scale_factor)
                h = int(self.roi_rect.height() / self.scale_factor)
                self.roi_drawn.emit((x, y, w, h))
                self.is_drawing = False


class STACaptureGUI(QMainWindow):
    """Main GUI Application - PySide6 Version"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("STA Screenshot Capture - PySide6")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(self._get_stylesheet())
        
        self.video_path = None
        self.cap = None
        self.video_fps = 0
        self.current_frame = None
        self.current_frame_idx = 0
        self.total_frames = 0
        self.video_width = 0
        self.video_height = 0
        self.preview_scale_factor = 1.0
        
        self.roi = None
        self.is_playing = False
        self.worker = None
        
        # Batch processing attributes
        self.batch_mode = False
        self.video_list = []
        self.current_batch_idx = 0
        self.batch_same_roi = True
        
        # Initialize EasyOCR reader for live preview (lazy - init after UI)
        self.ocr_reader = None
        
        self._init_ui()
        
        # NOW initialize OCR reader (after UI so any errors don't block UI)
        QTimer.singleShot(500, self._init_ocr_reader)
        
        self._check_tesseract()
        self._show_welcome()
        
    def _get_stylesheet(self):
        """Dark theme dengan accent oranye"""
        return """
            QMainWindow, QWidget { 
                background-color: #0f172a; 
                color: #e2e8f0; 
            }
            QTabWidget::pane { 
                border: 1px solid #1e293b; 
            }
            QTabBar::tab { 
                background-color: #1e293b; 
                color: #94a3b8; 
                padding: 8px 20px; 
            }
            QTabBar::tab:selected { 
                background-color: #f59e0b; 
                color: #000; 
            }
            
            QLabel { 
                color: #e2e8f0; 
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #1e293b; 
                color: #e2e8f0;
                border: 1px solid #334155; 
                border-radius: 4px; 
                padding: 6px;
                selection-background-color: #f59e0b;
            }
            QPushButton {
                background-color: #1e40af; 
                color: #fff; 
                border: none;
                border-radius: 4px; 
                padding: 8px 16px; 
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover { 
                background-color: #1e3a8a; 
            }
            QPushButton:pressed { 
                background-color: #172554; 
            }
            
            QPushButton#accentBtn {
                background-color: #f59e0b;
                color: #000;
            }
            QPushButton#accentBtn:hover { 
                background-color: #d97706; 
            }
            
            QTextEdit {
                background-color: #0f172a; 
                color: #10b981;
                border: 1px solid #1e293b; 
                border-radius: 4px;
                font-family: 'Courier New'; 
                font-size: 10px;
            }
            QGroupBox {
                color: #cbd5e1; 
                border: 1px solid #334155;
                border-radius: 4px; 
                padding: 12px; 
                margin-top: 12px;
            }
            QGroupBox::title { 
                subcontrol-origin: margin; 
                top: -6px; 
            }
            
            QProgressBar {
                border: 1px solid #334155; 
                border-radius: 4px;
                background-color: #1e293b;
                text-align: center;
            }
            QProgressBar::chunk { 
                background-color: #f59e0b; 
            }
            
            QStatusBar { 
                background-color: #1e293b; 
                color: #94a3b8;
            }
        """
    
    def _init_ui(self):
        """Initialize UI components"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        
        # Left panel: Video preview
        left_panel = self._create_left_panel()
        
        # Right panel: Tabs
        tabs = QTabWidget()
        tabs.addTab(self._create_video_settings_tab(), "📹 Video & ROI")
        tabs.addTab(self._create_batch_tab(), "📁 Batch")
        tabs.addTab(self._create_settings_tab(), "⚙️  Settings")
        tabs.addTab(self._create_processing_tab(), "▶️  Process")
        
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(tabs, 1)
        
        central_widget.setLayout(main_layout)
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")
    
    def _create_left_panel(self):
        """Video preview panel"""
        panel = QFrame()
        layout = QVBoxLayout()
        
        label = QLabel("📹 Video Preview")
        label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        
        self.preview_widget = VideoPreviewWidget()
        
        controls_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.clicked.connect(self._toggle_play)
        self.play_btn.setMaximumWidth(100)
        
        self.frame_slider = QSlider(Qt.Orientation.Horizontal)
        self.frame_slider.setMinimum(0)
        self.frame_slider.sliderMoved.connect(self._on_slider_moved)
        self.frame_slider.setTracking(False)
        
        self.frame_label = QLabel("0 / 0")
        self.frame_label.setMinimumWidth(100)
        self.frame_label.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.frame_slider, 1)
        controls_layout.addWidget(self.frame_label)
        
        layout.addWidget(label)
        layout.addWidget(self.preview_widget, 1)
        layout.addLayout(controls_layout)
        panel.setLayout(layout)
        
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self._update_preview)
        
        # Connect ROI drawing signal dari preview widget
        self.preview_widget.roi_drawn.connect(self._on_roi_drawn_from_preview)
        
        return panel
    
    def _create_video_settings_tab(self):
        """Tab untuk video input & ROI selection"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Debug path info
        debug_group = QGroupBox("📍 Video Path Debug")
        debug_layout = QVBoxLayout()
        self.debug_path_display = QTextEdit()
        self.debug_path_display.setReadOnly(True)
        self.debug_path_display.setMinimumHeight(60)
        self.debug_path_display.setMaximumHeight(80)
        self.debug_path_display.setStyleSheet("background-color: #0a0a0a; color: #10b981; font-size: 9px;")
        self.debug_path_display.setText("No video loaded yet\n\nSelected path will appear here")
        debug_layout.addWidget(self.debug_path_display)
        debug_group.setLayout(debug_layout)
        
        # Video selection group
        video_group = QGroupBox("Select Video")
        video_layout = QHBoxLayout()
        self.video_input = QLineEdit()
        self.video_input.setPlaceholderText("No video selected")
        self.video_input.setReadOnly(True)
        self.video_btn = QPushButton("Browse...")
        self.video_btn.clicked.connect(self._select_video)
        video_layout.addWidget(self.video_input)
        video_layout.addWidget(self.video_btn)
        video_group.setLayout(video_layout)
        
        # ROI group
        roi_group = QGroupBox("Define STA Text Region (ROI)")
        roi_layout = QGridLayout()
        
        roi_info = QLabel("Gambar ROI di preview video atau input manual koordinat pixel")
        roi_info.setStyleSheet("color: #94a3b8; font-size: 9px;")
        roi_layout.addWidget(roi_info, 0, 0, 1, 2)
        
        roi_labels = ["X", "Y", "Width", "Height"]
        self.roi_spinboxes = {}
        
        for i, label in enumerate(roi_labels):
            lbl = QLabel(f"{label}:")
            spin = QSpinBox()
            spin.setRange(0, 4000)
            spin.setValue(0)
            spin.valueChanged.connect(self._on_roi_changed)
            self.roi_spinboxes[label.lower()] = spin
            roi_layout.addWidget(lbl, i+1, 0)
            roi_layout.addWidget(spin, i+1, 1)
        
        self.roi_draw_btn = QPushButton("📍 Draw ROI on Preview")
        self.roi_draw_btn.setObjectName("accentBtn")
        self.roi_draw_btn.setCheckable(True)
        self.roi_draw_btn.clicked.connect(self._toggle_roi_drawing)
        roi_layout.addWidget(self.roi_draw_btn, 5, 0, 1, 2)
        
        roi_group.setLayout(roi_layout)
        
        # Live OCR preview
        ocr_group = QGroupBox("Live OCR Preview")
        ocr_layout = QVBoxLayout()
        self.ocr_display = QLabel("No frame loaded")
        self.ocr_display.setFont(QFont("Courier New", 16, QFont.Weight.Bold))
        self.ocr_display.setStyleSheet(
            "color: #f59e0b; background-color: #0a0a0a; padding: 15px; border-radius: 4px; border: 1px solid #f59e0b;"
        )
        self.ocr_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ocr_display.setMinimumHeight(80)
        ocr_layout.addWidget(self.ocr_display)
        ocr_group.setLayout(ocr_layout)
        
        layout.addWidget(debug_group)
        layout.addWidget(video_group)
        layout.addWidget(roi_group)
        layout.addWidget(ocr_group)
        layout.addStretch()
        
        # IMPORTANT: Set layout to tab!
        tab.setLayout(layout)
        return tab
    
    def _create_batch_tab(self):
        """Tab untuk batch processing dari folder"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Folder selection
        folder_group = QGroupBox("Select Folder Containing Videos")
        folder_layout = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("No folder selected")
        self.folder_input.setReadOnly(True)
        self.folder_btn = QPushButton("Browse Folder...")
        self.folder_btn.clicked.connect(self._select_folder)
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(self.folder_btn)
        folder_group.setLayout(folder_layout)
        
        # Video list
        list_group = QGroupBox("Videos Found")
        list_layout = QVBoxLayout()
        self.batch_video_list = QListWidget()
        self.batch_video_list.setMinimumHeight(150)
        list_layout.addWidget(self.batch_video_list)
        list_group.setLayout(list_layout)
        
        # ROI mode selection
        roi_mode_group = QGroupBox("ROI Settings for Batch")
        roi_mode_layout = QVBoxLayout()
        self.roi_mode_group = QButtonGroup()
        
        radio_same = QRadioButton("Use Same ROI for All Videos (from current selection)")
        radio_same.setChecked(True)
        radio_per = QRadioButton("Per-Video ROI (adjust for each video)")
        
        self.roi_mode_group.addButton(radio_same, 0)
        self.roi_mode_group.addButton(radio_per, 1)
        
        roi_mode_layout.addWidget(radio_same)
        roi_mode_layout.addWidget(radio_per)
        roi_info = QLabel(
            "ℹ️ Same ROI: Applies current ROI to all videos (best if all have same aspect ratio)\n"
            "Per-Video: Adjust ROI for each video before processing (slower but flexible)"
        )
        roi_info.setStyleSheet("color: #94a3b8; font-size: 9px;")
        roi_mode_layout.addWidget(roi_info)
        roi_mode_group.setLayout(roi_mode_layout)
        
        # Control buttons
        control_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("🔄 Refresh List")
        self.refresh_btn.clicked.connect(self._refresh_video_list)
        self.batch_start_btn = QPushButton("▶ Start Batch Processing")
        self.batch_start_btn.setObjectName("accentBtn")
        self.batch_start_btn.setMinimumHeight(40)
        self.batch_start_btn.clicked.connect(self._start_batch_processing)
        control_layout.addWidget(self.refresh_btn)
        control_layout.addWidget(self.batch_start_btn, 1)
        
        layout.addWidget(folder_group)
        layout.addWidget(list_group)
        layout.addWidget(roi_mode_group)
        layout.addLayout(control_layout)
        layout.addStretch()
        
        # IMPORTANT: Set layout to tab!
        tab.setLayout(layout)
        return tab
    
    def _create_settings_tab(self):
        """Tab untuk settings processing"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        settings_group = QGroupBox("Processing Parameters")
        settings_layout = QGridLayout()
        
        # Interval
        lbl_interval = QLabel("Capture Interval (meters):")
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(1, 1000)
        self.interval_spin.setValue(100)
        self.interval_spin.setSuffix(" m")
        settings_layout.addWidget(lbl_interval, 0, 0)
        settings_layout.addWidget(self.interval_spin, 0, 1)
        
        # Frame skip
        lbl_skip = QLabel("Frame Skip:")
        self.skip_spin = QSpinBox()
        self.skip_spin.setRange(1, 30)
        self.skip_spin.setValue(5)
        self.skip_spin.setSuffix(" frame")
        settings_layout.addWidget(lbl_skip, 1, 0)
        settings_layout.addWidget(self.skip_spin, 1, 1)
        
        # Output folder
        lbl_output = QLabel("Output Folder:")
        self.output_input = QLineEdit()
        self.output_input.setText(str(Path.home() / "STA_Output"))
        self.output_btn = QPushButton("Browse...")
        self.output_btn.clicked.connect(self._select_output)
        settings_layout.addWidget(lbl_output, 2, 0)
        settings_layout.addWidget(self.output_input, 2, 1)
        settings_layout.addWidget(self.output_btn, 2, 2)
        
        settings_group.setLayout(settings_layout)
        
        layout.addWidget(settings_group)
        layout.addStretch()
        
        # IMPORTANT: Set layout to tab!
        tab.setLayout(layout)
        return tab
    
    def _create_processing_tab(self):
        """Tab untuk processing & log"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Controls
        controls_layout = QHBoxLayout()
        self.process_btn = QPushButton("▶ Start Processing")
        self.process_btn.setObjectName("accentBtn")
        self.process_btn.setMinimumHeight(40)
        self.process_btn.clicked.connect(self._start_processing)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(40)
        self.stop_btn.clicked.connect(self._stop_processing)
        
        controls_layout.addWidget(self.process_btn, 1)
        controls_layout.addWidget(self.stop_btn, 1)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar { 
                border: 1px solid #334155; 
                border-radius: 4px; 
                background-color: #1e293b;
            }
            QProgressBar::chunk { 
                background-color: #10b981; 
            }
        """)
        self.progress_bar.setTextVisible(True)
        
        # Log display
        log_label = QLabel("📋 Processing Log:")
        log_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMinimumHeight(250)
        
        # Stats
        stats_label = QLabel("📊 Statistics:")
        stats_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.stats_display = QLabel("Waiting for processing...")
        self.stats_display.setStyleSheet("color: #94a3b8; padding: 10px; background-color: #1e293b; border-radius: 4px;")
        self.stats_display.setMinimumHeight(100)
        
        layout.addLayout(controls_layout)
        layout.addWidget(self.progress_bar)
        layout.addWidget(log_label)
        layout.addWidget(self.log_display, 1)
        layout.addWidget(stats_label)
        layout.addWidget(self.stats_display)
        
        # IMPORTANT: Set layout to tab!
        tab.setLayout(layout)
        return tab
    
    def _select_video(self):
        """Select video file"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Video", "", "Video Files (*.mp4 *.avi *.mov *.mkv *.flv *.wmv *.webm);;All Files (*)"
            )
            if file_path:
                if not os.path.isfile(file_path):
                    QMessageBox.warning(self, "Error", f"File not found: {file_path}")
                    self._update_debug_path("ERROR", file_path, "File not found")
                    return
                
                # Log ke console dan debug display
                abs_path = os.path.abspath(file_path)
                print(f"\n{'='*60}")
                print(f"VIDEO SELECTED")
                print(f"{'='*60}")
                print(f"Full Path: {abs_path}")
                print(f"Filename: {os.path.basename(file_path)}")
                print(f"Directory: {os.path.dirname(file_path)}")
                print(f"File exists: {os.path.isfile(abs_path)}")
                print(f"File size: {os.path.getsize(abs_path) / (1024*1024):.2f} MB")
                print(f"{'='*60}\n")
                
                self.video_path = file_path
                self.video_input.setText(file_path)
                self._update_debug_path("LOADED", abs_path, "Attempting to open...")
                self._load_video()
                self.statusBar().showMessage(f"✓ Video loaded: {Path(file_path).name}")
        except Exception as e:
            error_msg = f"Failed to select video: {str(e)}"
            print(f"ERROR: {error_msg}")
            QMessageBox.critical(self, "Error", error_msg)
            self._update_debug_path("ERROR", file_path if 'file_path' in locals() else "N/A", str(e))
    
    def _load_video(self):
        """Load video dan set properties"""
        if not self.video_path:
            return
        
        try:
            if self.cap:
                self.cap.release()
            
            self.cap = cv2.VideoCapture(self.video_path)
            
            # Check apakah video berhasil dibuka
            if not self.cap.isOpened():
                error_msg = f"Cannot open video: {self.video_path}"
                print(f"ERROR: {error_msg}")
                QMessageBox.critical(self, "Error", f"{error_msg}\n\nMake sure the file is a valid video file and not corrupted.")
                self._update_debug_path("FAILED", self.video_path, "Cannot open video file")
                self.cap = None
                self.video_path = None
                self.video_input.setText("")
                return
            
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.video_fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.video_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.video_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if self.total_frames <= 0 or self.video_width <= 0 or self.video_height <= 0:
                raise ValueError(f"Invalid video properties: {self.total_frames} frames, {self.video_width}x{self.video_height}")
            
            # Hitung scale factor untuk preview (640px lebar)
            self.preview_scale_factor = 640 / self.video_width if self.video_width > 0 else 1.0
            
            self.frame_slider.setMaximum(self.total_frames - 1)
            self._show_frame(0)
            
            info = f"Resolution: {self.video_width}x{self.video_height} | FPS: {self.video_fps:.2f} | Frames: {self.total_frames}"
            debug_info = f"{self.video_width}x{self.video_height} @ {self.video_fps:.2f} FPS\n{self.total_frames} frames"
            self._update_debug_path("SUCCESS", self.video_path, debug_info)
            
            print(f"VIDEO OPENED SUCCESSFULLY")
            print(f"Resolution: {self.video_width}x{self.video_height}")
            print(f"FPS: {self.video_fps:.2f}")
            print(f"Total Frames: {self.total_frames}")
            print(f"Scale Factor: {self.preview_scale_factor:.4f}")
            print()
            
            self.statusBar().showMessage(f"✓ Video loaded: {info}")
            
        except Exception as e:
            error_msg = f"Cannot load video: {str(e)}"
            print(f"ERROR: {error_msg}")
            QMessageBox.critical(self, "Error Loading Video", error_msg)
            self._update_debug_path("ERROR", self.video_path, str(e))
            self.cap = None
            self.video_path = None
            self.video_input.setText("")
    
    def _show_frame(self, frame_idx):
        """Display specific frame"""
        if not self.cap or not self.cap.isOpened():
            self.preview_widget.label.setText("No video loaded")
            return
        
        try:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = self.cap.read()
            
            if not ret or frame is None:
                self.preview_widget.label.setText(f"Cannot read frame {frame_idx}")
                return
            
            self.current_frame = frame
            self.current_frame_idx = frame_idx
            
            # Convert to RGB dan resize untuk preview
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = 3 * w
            qt_img = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_img)
            
            # Scale untuk fit widget
            scaled_pixmap = pixmap.scaledToWidth(640, Qt.TransformationMode.SmoothTransformation)
            
            self.preview_widget.set_pixmap(scaled_pixmap, self.roi, self.preview_scale_factor)
            self.frame_label.setText(f"{frame_idx + 1} / {self.total_frames}")
            
            # Show live OCR
            if self.roi:
                self._update_ocr_preview(frame)
        except Exception as e:
            self.preview_widget.label.setText(f"Error: {str(e)}")
    
    def _update_ocr_preview(self, frame):
        """Update live OCR preview with EasyOCR"""
        try:
            if not self.roi or not all(self.roi):
                return
                
            x, y, w, h = self.roi
            # Validate ROI bounds
            frame_h, frame_w = frame.shape[:2]
            if x + w > frame_w or y + h > frame_h:
                self.ocr_display.setText("ROI out of bounds for this video")
                return
                
            roi_img = frame[y:y + h, x:x + w]
            
            try:
                if self.ocr_reader is None:
                    self.ocr_display.setText("EasyOCR not initialized...")
                    return
                
                # Use EasyOCR for preview (handles preprocessing internally)
                results = self.ocr_reader.readtext(roi_img, detail=0)
                text = ''.join(results).strip()
                self.ocr_display.setText(text if text else "No text detected")
            except Exception as ocr_err:
                self.ocr_display.setText(f"OCR Error: {str(ocr_err)[:50]}")
        except Exception as e:
            self.ocr_display.setText(f"Error: {str(e)[:50]}")

    
    def _update_preview(self):
        """Timer callback untuk auto-play"""
        if self.is_playing and self.current_frame_idx < self.total_frames - 1:
            self._show_frame(self.current_frame_idx + 1)
            self.frame_slider.blockSignals(True)
            self.frame_slider.setValue(self.current_frame_idx)
            self.frame_slider.blockSignals(False)
    
    def _toggle_play(self):
        """Toggle play/pause"""
        if not self.cap:
            QMessageBox.warning(self, "Warning", "Please select a video first")
            return
        
        self.is_playing = not self.is_playing
        self.play_btn.setText("⏸ Pause" if self.is_playing else "▶ Play")
        
        if self.is_playing:
            self.preview_timer.start(int(1000 / self.video_fps) if self.video_fps > 0 else 33)
        else:
            self.preview_timer.stop()
    
    def _on_slider_moved(self, value):
        """Slider moved"""
        self._show_frame(value)
    
    def _on_roi_changed(self):
        """ROI spinbox changed"""
        x = self.roi_spinboxes['x'].value()
        y = self.roi_spinboxes['y'].value()
        w = self.roi_spinboxes['width'].value()
        h = self.roi_spinboxes['height'].value()
        
        if x >= 0 and y >= 0 and w > 0 and h > 0:
            self.roi = (x, y, w, h)
            if self.current_frame is not None:
                self._show_frame(self.current_frame_idx)
    
    def _select_output(self):
        """Select output folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_input.setText(folder)
    
    def _select_folder(self):
        """Select folder containing videos"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder with Videos")
        if folder:
            self.folder_input.setText(folder)
            self._refresh_video_list()
    
    def _refresh_video_list(self):
        """Scan folder dan list semua video files"""
        self.batch_video_list.clear()
        self.video_list = []
        
        folder_path = self.folder_input.text()
        if not folder_path or not os.path.isdir(folder_path):
            QMessageBox.warning(self, "Warning", "Please select a valid folder first")
            return
        
        # Video extensions
        video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm')
        
        try:
            folder = Path(folder_path)
            video_files = sorted([f for f in folder.iterdir() 
                                 if f.is_file() and f.suffix.lower() in video_extensions])
            
            if not video_files:
                QMessageBox.information(self, "Info", f"No video files found in {folder_path}")
                return
            
            for video_file in video_files:
                item = QListWidgetItem(video_file.name)
                item.setCheckState(Qt.CheckState.Checked)
                self.batch_video_list.addItem(item)
                self.video_list.append(str(video_file))
            
            self.statusBar().showMessage(f"✓ Found {len(self.video_list)} video(s)")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error scanning folder: {str(e)}")
    
    def _start_batch_processing(self):
        """Start batch processing dari folder"""
        if not self.video_list:
            QMessageBox.warning(self, "Warning", "No videos in list. Please select folder first.")
            return
        
        # Check yang mana yang dipilih
        selected_videos = []
        for idx in range(self.batch_video_list.count()):
            item = self.batch_video_list.item(idx)
            if item.checkState() == Qt.CheckState.Checked:
                selected_videos.append(self.video_list[idx])
        
        if not selected_videos:
            QMessageBox.warning(self, "Warning", "Please select at least one video to process")
            return
        
        # Check ROI
        if not self.roi or not all(self.roi):
            QMessageBox.warning(self, "Warning", "⚠️ Please define ROI first (use Video & ROI tab)")
            return
        
        # Check output folder
        output_folder = self.output_input.text()
        try:
            Path(output_folder).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Cannot create output folder: {str(e)}")
            return
        
        # Setup batch mode
        self.batch_mode = True
        self.batch_same_roi = self.roi_mode_group.checkedId() == 0
        self.current_batch_idx = 0
        
        if self.batch_same_roi:
            # Proses semua dengan ROI yang sama
            self._process_batch_same_roi(selected_videos, output_folder)
        else:
            # Proses per-video
            self._process_batch_per_video(selected_videos, output_folder)
    
    def _process_batch_same_roi(self, video_list, output_folder):
        """Process batch dengan same ROI untuk semua"""
        self.current_batch_idx = 0
        self._process_next_batch_video(video_list, output_folder)
    
    def _process_batch_per_video(self, video_list, output_folder):
        """Process batch dengan per-video ROI adjustment"""
        QMessageBox.information(
            self,
            "Per-Video ROI Mode",
            "You will be prompted to adjust ROI for each video.\n"
            "Define ROI in 'Video & ROI' tab for each video, then start processing."
        )
        # Load first video
        self.video_path = video_list[0]
        self.video_input.setText(video_list[0])
        self._load_video()
        self.statusBar().showMessage(f"Adjust ROI for: {Path(video_list[0]).name}")
    
    def _process_next_batch_video(self, video_list, output_folder):
        """Process next video dalam batch dengan same ROI"""
        if self.current_batch_idx >= len(video_list):
            QMessageBox.information(self, "Complete", "Batch processing completed!")
            self.batch_mode = False
            return
        
        video_path = video_list[self.current_batch_idx]
        video_name = Path(video_path).stem
        
        # Create output subfolder per video
        video_output = os.path.join(output_folder, video_name)
        
        try:
            Path(video_output).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.log_display.append(f"❌ Error creating output for {video_name}: {str(e)}")
            self.current_batch_idx += 1
            self._process_next_batch_video(video_list, output_folder)
            return
        
        # Process video
        self.worker = ProcessWorker(
            video_path,
            self.roi,
            self.interval_spin.value(),
            video_output,
            self.skip_spin.value(),
            video_name,
            batch_size=6  # Optimal untuk GTX 1050
        )
        self.worker.signals.progress.connect(self._on_progress)
        self.worker.signals.log.connect(self._on_log)
        self.worker.signals.stats.connect(self._on_stats)
        self.worker.signals.finished.connect(lambda: self._on_batch_video_finished(video_list, output_folder))
        
        self.process_btn.setEnabled(False)
        self.batch_start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.log_display.clear()
        self.log_display.append(f"🔄 Processing batch video {self.current_batch_idx + 1}/{len(video_list)}...\n")
        self.progress_bar.setValue(0)
        
        self.worker.start()
        self.statusBar().showMessage(f"Processing: {video_name}")
    
    def _on_batch_video_finished(self, video_list, output_folder):
        """Called when batch video processing finished"""
        self.current_batch_idx += 1
        if self.current_batch_idx < len(video_list):
            self.log_display.append(f"\n✅ Completed. Moving to next video...\n")
            self._process_next_batch_video(video_list, output_folder)
        else:
            self.log_display.append("\n" + "="*50)
            self.log_display.append(f"✅ ALL BATCH PROCESSING COMPLETED ({len(video_list)} videos)!")
            self.log_display.append("="*50)
            self.process_btn.setEnabled(True)
            self.batch_start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.batch_mode = False
            self.statusBar().showMessage("✓ Batch processing completed")
    
    def _toggle_roi_drawing(self):
        """Toggle ROI drawing mode"""
        if not self.cap:
            QMessageBox.warning(self, "Warning", "Please select a video first")
            self.roi_draw_btn.setChecked(False)
            return
        
        self.preview_widget.is_drawing = self.roi_draw_btn.isChecked()
        if self.roi_draw_btn.isChecked():
            self.roi_draw_btn.setText("📍 Drawing... (Drag to select)")
            self.statusBar().showMessage("Drag ROI area on preview")
        else:
            self.roi_draw_btn.setText("📍 Draw ROI on Preview")
            self.statusBar().showMessage("Ready")
    
    def _on_roi_drawn_from_preview(self, roi_tuple):
        """Update roi_spinboxes from drawn ROI di preview"""
        x, y, w, h = roi_tuple
        self.roi_spinboxes['x'].blockSignals(True)
        self.roi_spinboxes['y'].blockSignals(True)
        self.roi_spinboxes['width'].blockSignals(True)
        self.roi_spinboxes['height'].blockSignals(True)
        
        self.roi_spinboxes['x'].setValue(x)
        self.roi_spinboxes['y'].setValue(y)
        self.roi_spinboxes['width'].setValue(w)
        self.roi_spinboxes['height'].setValue(h)
        
        self.roi_spinboxes['x'].blockSignals(False)
        self.roi_spinboxes['y'].blockSignals(False)
        self.roi_spinboxes['width'].blockSignals(False)
        self.roi_spinboxes['height'].blockSignals(False)
        
        self._on_roi_changed()
        self.roi_draw_btn.setChecked(False)
        self._toggle_roi_drawing()
    
    def _init_ocr_reader(self):
        """Initialize EasyOCR reader for live preview (async safe)"""
        try:
            import easyocr
            self.ocr_reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available())
            self.statusBar().showMessage("✅ OCR reader ready for live preview")
        except Exception as e:
            self.ocr_reader = None
            self.statusBar().showMessage(f"⚠️ Live OCR preview unavailable: {str(e)[:50]}")
            print(f"OCR Reader initialization failed: {e}")
    
    def _check_tesseract(self):
        """Check if EasyOCR and dependencies are installed"""
        try:
            import easyocr
            import torch
            gpu_available = torch.cuda.is_available()
            device_msg = f"CUDA GPU ({torch.cuda.get_device_name(0)})" if gpu_available else "CPU"
            self.statusBar().showMessage(f"✅ EasyOCR ready | Device: {device_msg}")
            return True
        except ImportError as e:
            QMessageBox.warning(
                self,
                "EasyOCR Dependencies Not Found",
                "EasyOCR or required dependencies are not installed.\n\n"
                "To install, run in terminal:\n"
                "  pip install easyocr torch torchvision\n\n"
                "For GPU support (NVIDIA):\n"
                "  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118\n\n"
                "After installation, restart this application."
            )
            return False
        except Exception as e:
            self.statusBar().showMessage(f"⚠️  EasyOCR check warning: {str(e)}")
            return False
    
    def _show_welcome(self):
        """Show welcome message dengan instruksi penggunaan"""
        welcome_msg = (
            "Welcome to STA Screenshot Capture!\n\n"
            "QUICK START:\n"
            "1. Go to 'Video & ROI' tab → Click 'Browse...' to select a video\n"
            "2. Define ROI area (Region of Interest) where STA text is located\n"
            "   - Drag directly on preview, OR\n"
            "   - Enter X, Y, Width, Height coordinates manually\n"
            "3. Go to 'Settings' tab → Configure capture interval and output folder\n"
            "4. Go to 'Process' tab → Click 'Start Processing'\n\n"
            "FOR BATCH PROCESSING:\n"
            "1. Go to 'Batch' tab → Click 'Browse Folder...' to select folder with multiple videos\n"
            "2. Select which videos to process (use checkboxes)\n"
            "3. Choose ROI mode: Same ROI for all, or Per-Video adjustment\n"
            "4. Click 'Start Batch Processing'\n\n"
            "Supported formats: MP4, AVI, MOV, MKV, FLV, WMV, WEBM\n"
            "Supported resolutions: Any (up to 4K)"
        )
        QMessageBox.information(self, "Getting Started", welcome_msg)
    
    def _update_debug_path(self, status, path, details=""):
        """Update debug path display with status"""
        debug_text = f"[{status}]\n"
        debug_text += f"Path: {path}\n"
        if details:
            debug_text += f"Info: {details}"
        self.debug_path_display.setText(debug_text)
    
    def _start_processing(self):
        """Start video processing"""
        # Validation
        if not self.video_path:
            QMessageBox.warning(self, "Warning", "⚠️ Please select a video")
            return
        if not self.roi or not all(self.roi):
            QMessageBox.warning(self, "Warning", "⚠️ Please define ROI (X, Y, Width, Height)")
            return
        
        output_folder = self.output_input.text()
        try:
            Path(output_folder).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"❌ Cannot create output folder: {str(e)}")
            return
        
        # Start worker
        self.worker = ProcessWorker(
            self.video_path,
            self.roi,
            self.interval_spin.value(),
            output_folder,
            self.skip_spin.value(),
            Path(self.video_path).stem,
            batch_size=6  # Optimal untuk GTX 1050
        )
        self.worker.signals.progress.connect(self._on_progress)
        self.worker.signals.log.connect(self._on_log)
        self.worker.signals.stats.connect(self._on_stats)
        self.worker.signals.finished.connect(self._on_finished)
        
        self.process_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.log_display.clear()
        self.log_display.append("🔄 Processing dimulai...\n")
        self.progress_bar.setValue(0)
        
        self.worker.start()
        self.statusBar().showMessage("Processing in progress...")
    
    def _stop_processing(self):
        """Stop processing"""
        if self.worker:
            self.worker.stop()
            self.log_display.append("⏹️  Stopping processing...")
            if not self.batch_mode:
                self.stop_btn.setEnabled(False)
                self.process_btn.setEnabled(True)
    
    def _on_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)
    
    def _on_log(self, message):
        """Add log message"""
        self.log_display.append(message)
        # Auto-scroll to bottom
        self.log_display.verticalScrollBar().setValue(
            self.log_display.verticalScrollBar().maximum()
        )
    
    def _on_stats(self, stats):
        """Display statistics"""
        msg = f"""
        <b>Screenshots Saved:</b> {stats['saved']}<br>
        <b>OCR Attempts:</b> {stats['attempts']}<br>
        <b>OCR Success:</b> {stats['success']}<br>
        <b>OCR Accuracy:</b> {stats['accuracy']:.1f}%
        """
        self.stats_display.setText(msg)
    
    def _on_finished(self):
        """Processing finished"""
        self.process_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.log_display.append("\n✅ Processing selesai!")
        self.statusBar().showMessage("✓ Processing completed")
    
    def closeEvent(self, event):
        """Cleanup on close"""
        if self.preview_timer.isActive():
            self.preview_timer.stop()
        if self.cap:
            self.cap.release()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = STACaptureGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
