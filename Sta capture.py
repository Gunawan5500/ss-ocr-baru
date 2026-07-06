"""
Prototype: capture screenshot otomatis dari video berdasarkan overlay STA,
setiap kali nilai STA melewati kelipatan interval tertentu (default 100 m).

Cara pakai:
    python3 sta_capture.py video.mp4 --roi 10 310 220 40 --output hasil

Catatan:
- --roi diisi x y w h dari area teks STA di frame video (dalam piksel).
- Format STA yang dikenali: "STA <km>+<meter>", misal "STA 12+300".
"""
import argparse
import os
import re

import cv2
import pytesseract

STA_REGEX = re.compile(r'(\d{1,4})\s*\+\s*(\d{1,3}(?:\.\d{1,2})?)')


def parse_sta(text):
    """Ekstrak nilai jarak (meter) dari teks hasil OCR, format 'km+meter'."""
    match = STA_REGEX.search(text)
    if not match:
        return None
    km = int(match.group(1))
    m = float(match.group(2))
    return km * 1000 + m


def preprocess(roi_img, scale=3):
    """Perbesar & bersihkan gambar ROI supaya OCR lebih akurat."""
    gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh


def ocr_read(img):
    config = '--psm 7 -c tessedit_char_whitelist=0123456789+.STA'
    text = pytesseract.image_to_string(img, config=config)
    return text.strip()


def main():
    parser = argparse.ArgumentParser(
        description='Capture screenshot per interval jarak (meter) berdasarkan overlay STA pada video')
    parser.add_argument('video', help='Path video input')
    parser.add_argument('--roi', nargs=4, type=int, metavar=('X', 'Y', 'W', 'H'), required=True,
                         help='Area (x y w h) tempat teks STA berada, dalam piksel')
    parser.add_argument('--interval', type=float, default=100, help='Interval capture dalam meter (default 100)')
    parser.add_argument('--output', default='output', help='Folder output screenshot')
    parser.add_argument('--frame-skip', type=int, default=5,
                         help='Proses tiap N frame untuk mempercepat (default 5)')
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print(f'Gagal membuka video: {args.video}')
        return

    x, y, w, h = args.roi
    frame_idx = 0
    last_saved_multiple = None
    last_value = None
    saved_count = 0
    read_attempts = 0
    read_success = 0

    print('Memulai proses...')
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % args.frame_skip == 0:
            roi_img = frame[y:y + h, x:x + w]
            proc = preprocess(roi_img)
            text = ocr_read(proc)
            value = parse_sta(text)
            read_attempts += 1

            if value is not None:
                read_success += 1
                # validasi: tolak lompatan nilai yang tidak wajar (kemungkinan salah baca OCR)
                if last_value is not None:
                    diff = value - last_value
                    if diff < -5 or diff > args.interval * 5:
                        frame_idx += 1
                        continue
                last_value = value

                current_multiple = int(value // args.interval) * args.interval
                if last_saved_multiple is None or current_multiple > last_saved_multiple:
                    last_saved_multiple = current_multiple
                    km = int(current_multiple // 1000)
                    m = int(current_multiple % 1000)
                    filename = f'STA_{km}+{m:03d}.jpg'
                    filepath = os.path.join(args.output, filename)
                    cv2.imwrite(filepath, frame)
                    saved_count += 1
                    print(f'  Tersimpan: {filename}  (OCR baca: "{text}")')

        frame_idx += 1

    cap.release()
    print('---')
    print(f'Selesai. Total {saved_count} screenshot tersimpan di folder "{args.output}"')
    if read_attempts:
        print(f'Tingkat keberhasilan OCR: {read_success}/{read_attempts} '
              f'({100 * read_success / read_attempts:.1f}%)')


if __name__ == '__main__':
    main()