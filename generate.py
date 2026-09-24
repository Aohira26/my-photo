import os
import shutil
import cv2
from PIL import Image

# ------------------------------------
# 設定
# ------------------------------------
STORAGE_PATH = 'E:\写真\旅行'  # 対象のフォルダパス（必要に応じて変更してください）
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
THUMB_DIR = os.path.join(OUTPUT_DIR, 'thumbnails')

# 既存のthumbnailsフォルダを一旦クリーンアップ
if os.path.exists(THUMB_DIR):
    shutil.rmtree(THUMB_DIR)
os.makedirs(THUMB_DIR, exist_ok=True)

html_content = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>外付けSSD キャッシュ一覧</title>
    <style>
        body { font-family: sans-serif; background: #121212; color: #fff; padding: 15px; margin: 0; }
        h2 { border-bottom: 2px solid #333; padding-bottom: 10px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 10px; }
        .card { background: #1e1e1e; border-radius: 8px; overflow: hidden; padding: 8px; text-align: center; border: 1px solid #333; }
        .card img { width: 100%; height: 100px; object-fit: cover; border-radius: 4px; }
        .icon { height: 100px; line-height: 100px; font-size: 30px; background: #2a2a2a; border-radius: 4px; }
        .filename { font-size: 11px; margin-top: 6px; word-break: break-all; color: #ccc; }
    </style>
</head>
<body>
    <h2>📁 外付けSSD キャッシュ一覧</h2>
    <div class="grid">
"""

if os.path.exists(STORAGE_PATH):
    for root, dirs, files in os.walk(STORAGE_PATH):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, STORAGE_PATH)
            ext = os.path.splitext(file)[1].lower()
            
            thumb_name = rel_path.replace("\\", "_").replace("/", "_") + ".jpg"
            thumb_path = os.path.join(THUMB_DIR, thumb_name)
            
            has_thumb = False
            
            # 画像のサムネイル作成
            if ext in ['.jpg', '.jpeg', '.png', '.webp', '.bmp']:
                try:
                    with Image.open(file_path) as img:
                        img.thumbnail((200, 200))
                        img.save(thumb_path, "JPEG", quality=70)
                        has_thumb = True
                except: pass
                
            # 動画のサムネイル作成
            elif ext in ['.mp4', '.mkv', '.mov', '.avi', '.wmv']:
                try:
                    cap = cv2.VideoCapture(file_path)
                    ret, frame = cap.read()
                    if ret:
                        cv2.imwrite(thumb_path, frame)
                        has_thumb = True
                    cap.release()
                except: pass

            # HTML出力
            html_content += '<div class="card">'
            if has_thumb:
                html_content += f'<img src="thumbnails/{thumb_name}" alt="{file}">'
            else:
                html_content += f'<div class="icon">📄</div>'
            html_content += f'<div class="filename">{rel_path}</div></div>\n'
else:
    html_content += '<p>※指定されたフォルダが見つかりません。</p>'

html_content += """
    </div>
</body>
</html>
"""

with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(html_content)

print("サムネイルとindex.htmlの生成が完了しました！")