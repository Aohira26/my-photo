import os
import sys
import shutil
import json
import cv2
from PIL import Image
from pillow_heif import register_heif_opener
from concurrent.futures import ProcessPoolExecutor

# HEIC形式の読み込みをPillowに登録
register_heif_opener()

# ------------------------------------
# 設定
# ------------------------------------
STORAGE_PATH = r'E:\写真\旅行'  # 対象のフォルダパス
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
THUMB_DIR = os.path.join(OUTPUT_DIR, 'thumbnails')
CACHE_FILE = os.path.join(OUTPUT_DIR, 'file_cache.json')

def process_file(args):
    file_path, rel_path, THUMB_DIR = args
    ext = os.path.splitext(file_path)[1].lower()
    # 拡張子部分（.MOV等）を取り除いてから .jpg を付ける
    base_rel_path = os.path.splitext(rel_path)[0]
    thumb_name = base_rel_path.replace("\\", "_").replace("/", "_") + ".jpg"
    thumb_path = os.path.join(THUMB_DIR, thumb_name)
    has_thumb = False

    # 画像ファイル（.heic や .jpg, .png など）
    if ext in ['.jpg', '.jpeg', '.png', '.webp', '.bmp', '.heic']:
        try:
            with Image.open(file_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.thumbnail((180, 180))
                img.save(thumb_path, "JPEG", quality=65, optimize=True)
                has_thumb = True
        except: pass

    # 動画ファイル（.mov, .mp4 など）
    elif ext in ['.mp4', '.mkv', '.mov', '.avi', '.wmv', '.m4v']:
        try:
            cap = cv2.VideoCapture(file_path)
            # 最初の数フレームをスキップして確実に画像をキャプチャ
            for _ in range(5):
                ret, frame = cap.read()
                if not ret:
                    break
            if ret and frame is not None:
                h, w = frame.shape[:2]
                new_w = 180
                new_h = int(h * (180 / w))
                resized = cv2.resize(frame, (new_w, new_h))
                cv2.imwrite(thumb_path, resized, [int(cv2.IMWRITE_JPEG_QUALITY), 65])
                has_thumb = True
            cap.release()
        except: pass

    return rel_path, thumb_name, has_thumb

def build_tree(results):
    tree = {"_files": [], "_subfolders": {}}
    for rel_path, thumb_name, has_thumb in results:
        parts = rel_path.replace("\\", "/").split("/")
        filename = parts[-1]
        folders = parts[:-1]
        
        current = tree
        for folder in folders:
            if folder not in current["_subfolders"]:
                current["_subfolders"][folder] = {"_files": [], "_subfolders": {}}
            current = current["_subfolders"][folder]
        
        current["_files"].append({
            "name": filename,
            "rel_path": rel_path,
            "thumb_name": thumb_name,
            "has_thumb": has_thumb
        })
    return tree

def render_folder_html(folder_dict, path_prefix=""):
    html = ""
    for folder_name, content in sorted(folder_dict["_subfolders"].items()):
        current_path = f"{path_prefix}/{folder_name}" if path_prefix else folder_name
        html += f'''
        <details class="folder-group" open>
            <summary class="folder-header">
                <span class="icon">📁</span>
                <span class="folder-title">{folder_name}</span>
                <span class="count">({len(content["_files"])}件)</span>
            </summary>
            <div class="folder-content">
        '''
        html += render_folder_html(content, current_path)
        html += '</div></details>'
        
    if folder_dict["_files"]:
        html += '<div class="grid">'
        for file in folder_dict["_files"]:
            html += '<div class="card">'
            if file["has_thumb"]:
                html += f'<img src="thumbnails/{file["thumb_name"]}" alt="{file["name"]}" loading="lazy">'
            else:
                html += '<div class="file-icon">📄</div>'
            html += f'<div class="filename">{file["name"]}</div></div>\n'
        html += '</div>'
        
    return html

def main():
    if not os.path.exists(STORAGE_PATH):
        print(f"※指定されたフォルダが見つかりません: {STORAGE_PATH}")
        sys.exit(1)

    print("📁 ファイル一覧を取得中...")
    current_files = []
    file_tasks = []
    for root, dirs, files in os.walk(STORAGE_PATH):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, STORAGE_PATH)
            current_files.append(rel_path)
            file_tasks.append((file_path, rel_path, THUMB_DIR))

    current_files.sort()
    total_files = len(current_files)

    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                old_files = json.load(f)
            if old_files == current_files:
                print(f"相違なし: ファイル数（{total_files}件）に変更がないため処理をスキップします。")
                sys.exit(100)
        except: pass

    if os.path.exists(THUMB_DIR):
        shutil.rmtree(THUMB_DIR)
    os.makedirs(THUMB_DIR, exist_ok=True)

    print(f"📸 変更を検出しました（全 {total_files} 件）。サムネイル作成を開始します...")
    results = []
    with ProcessPoolExecutor() as executor:
        for i, res in enumerate(executor.map(process_file, file_tasks), 1):
            results.append(res)
            if i % 50 == 0 or i == total_files:
                print(f"処理中... [{i}/{total_files}] ({(i/total_files)*100:.1f}%)")

    print("📝 エクスプローラー風HTMLを構築中...")
    tree = build_tree(results)
    explorer_body = render_folder_html(tree)

    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SSD エクスプローラー View</title>
    <style>
        :root {{
            --bg-color: #181818;
            --card-bg: #252526;
            --border-color: #3f3f46;
            --text-color: #f4f4f5;
            --sub-text: #a1a1aa;
            --accent-color: #007acc;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 15px;
        }}
        header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 10px;
            margin-bottom: 15px;
        }}
        h2 {{
            margin: 0;
            font-size: 1.2rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .folder-group {{
            margin-bottom: 10px;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            background: #1e1e1e;
            overflow: hidden;
        }}
        .folder-header {{
            padding: 10px 14px;
            background: #2d2d30;
            cursor: pointer;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 8px;
            user-select: none;
        }}
        .folder-header:hover {{
            background: #3e3e42;
        }}
        .folder-title {{
            color: #569cd6;
        }}
        .count {{
            font-size: 0.8rem;
            color: var(--sub-text);
            font-weight: normal;
        }}
        .folder-content {{
            padding: 12px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 10px;
        }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 6px;
            text-align: center;
            transition: transform 0.1s ease;
        }}
        .card:hover {{
            border-color: var(--accent-color);
            transform: translateY(-2px);
        }}
        .card img {{
            width: 100%;
            height: 90px;
            object-fit: cover;
            border-radius: 4px;
        }}
        .file-icon {{
            height: 90px;
            line-height: 90px;
            font-size: 28px;
            background: #1a1a1a;
            border-radius: 4px;
        }}
        .filename {{
            font-size: 11px;
            margin-top: 6px;
            word-break: break-all;
            color: #d4d4d4;
            line-height: 1.2;
        }}
    </style>
</head>
<body>
    <header>
        <h2>📁 外付けSSD キャッシュ一覧</h2>
    </header>
    <main>
        {explorer_body}
    </main>
</body>
</html>
"""

    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html_content)

    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(current_files, f, ensure_ascii=False, indent=2)

    print("✨ エクスプローラー風HTMLの高速生成が完了しました！")

if __name__ == '__main__':
    main()