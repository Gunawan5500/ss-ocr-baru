"""
Interactive ROI Finder - Mudah untuk test dan adjust ROI
"""

import cv2
import numpy as np
import sys

video_path = input("Video path: ").strip()
if not video_path:
    video_path = "10.001.12 L1.mp4"

cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print(f"❌ Cannot open: {video_path}")
    sys.exit(1)

ret, frame = cap.read()
if not ret:
    print("❌ Cannot read frame")
    sys.exit(1)

# Default ROI
roi = {'x': 0, 'y': 0, 'w': 400, 'h': 100}
drawing = False

def draw_roi(img, roi):
    """Draw ROI rectangle on image"""
    img_copy = img.copy()
    x, y, w, h = roi['x'], roi['y'], roi['w'], roi['h']
    cv2.rectangle(img_copy, (x, y), (x+w, y+h), (0, 255, 0), 3)
    cv2.putText(img_copy, f"ROI: ({x}, {y}, {w}, {h})", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    return img_copy

def mouse_callback(event, x, y, flags, param):
    """Mouse callback for ROI adjustment"""
    global drawing
    
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        roi['x'] = min(x, roi['x'] + roi['w'])
        roi['y'] = min(y, roi['y'] + roi['h'])
    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        roi['w'] = abs(x - roi['x'])
        roi['h'] = abs(y - roi['y'])

cv2.namedWindow('ROI Finder')
cv2.setMouseCallback('ROI Finder', mouse_callback)

print("\n" + "="*70)
print("INTERACTIVE ROI FINDER")
print("="*70)
print("1. Drag mouse to select ROI area (capture STA text)")
print("2. Use these keys:")
print("   - 'ARROW UP': Move ROI up by 10px")
print("   - 'ARROW DOWN': Move ROI down by 10px")
print("   - 'ARROW LEFT': Move ROI left by 10px")
print("   - 'ARROW RIGHT': Move ROI right by 10px")
print("   - '+' / '-': Increase/Decrease width by 10px")
print("   - '*' / '/': Increase/Decrease height by 10px")
print("   - 'R': Reset to default")
print("   - 'S': Save ROI and show extracted image")
print("   - 'Q': Quit")
print("="*70 + "\n")

while True:
    display = draw_roi(frame, roi)
    
    # Resize for display
    h, w = display.shape[:2]
    if w > 1200:
        scale = 1200 / w
        display = cv2.resize(display, (int(w*scale), int(h*scale)))
    
    cv2.imshow('ROI Finder', display)
    
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('q'):
        break
    elif key == ord('r'):
        roi = {'x': 0, 'y': 0, 'w': 400, 'h': 100}
    elif key == ord('s'):
        x, y, w, h = roi['x'], roi['y'], roi['w'], roi['h']
        roi_img = frame[y:y+h, x:x+w]
        
        print(f"\n✓ ROI: x={x}, y={y}, w={w}, h={h}")
        print(f"✓ ROI image shape: {roi_img.shape}")
        
        # Show ROI
        cv2.imshow('Extracted ROI', roi_img)
        
        # Save
        cv2.imwrite('roi_extracted.jpg', roi_img)
        print(f"✓ Saved: roi_extracted.jpg\n")
        
        # Test OCR
        try:
            import pytesseract
            text = pytesseract.image_to_string(roi_img)
            print(f"OCR Result:\n{text}\n")
        except:
            print("(Tesseract not available)\n")
    
    elif key == 82:  # UP
        roi['y'] = max(0, roi['y'] - 10)
    elif key == 84:  # DOWN
        roi['y'] = min(frame.shape[0] - roi['h'], roi['y'] + 10)
    elif key == 81:  # LEFT
        roi['x'] = max(0, roi['x'] - 10)
    elif key == 83:  # RIGHT
        roi['x'] = min(frame.shape[1] - roi['w'], roi['x'] + 10)
    elif key == ord('+') or key == ord('='):
        roi['w'] = min(frame.shape[1] - roi['x'], roi['w'] + 10)
    elif key == ord('-') or key == ord('_'):
        roi['w'] = max(10, roi['w'] - 10)
    elif key == ord('*'):
        roi['h'] = min(frame.shape[0] - roi['y'], roi['h'] + 10)
    elif key == ord('/'):
        roi['h'] = max(10, roi['h'] - 10)

cv2.destroyAllWindows()
cap.release()

print("Done!")
