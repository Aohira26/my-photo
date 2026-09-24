@echo off
cd /d C:\ssd-viewer\my-photo

:: SSD（Eドライブ）が接続されているか確認
if not exist "E:\" (
    echo 外付けSSDが接続されていないため、処理をスキップします。
    timeout /t 3
    exit
)

echo [1/4] チェック中...
python generate.py

:: 変更がなかった場合（エラーコード100）はスキップして終了
if %errorlevel% equ 100 (
    echo.
    echo 変更がないため、GitHubへの送信をスキップします。
    timeout /t 2
    exit
)

echo [2/4] Gitに追加中...
git add index.html thumbnails file_cache.json

echo [3/4] GitHubへ送信中...
git commit -m "Auto update on startup"
git push origin main

echo [4/4] ローカルのサムネイルを削除中...
rd /s /q thumbnails

echo 完了しました！画面を閉じます。
timeout /t 3