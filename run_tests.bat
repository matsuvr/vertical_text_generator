@echo off
REM 日本語縦書きAPI テスト実行バッチファイル
REM 使用方法: run_tests.bat

echo ===================================
echo 日本語縦書きAPI テスト実行
echo ===================================

REM 現在のディレクトリを保存
set CURRENT_DIR=%CD%

REM スクリプトのディレクトリに移動
cd /d "%~dp0"

REM 仮想環境の確認
if not exist ".venv\Scripts\python.exe" (
    echo エラー: 仮想環境が見つかりません
    echo .venv\Scripts\python.exe が存在することを確認してください
    pause
    exit /b 1
)

REM APIサーバーが起動しているかチェック
echo APIサーバーの起動状況をチェック中...
.venv\Scripts\python.exe -c "import requests; requests.get('http://localhost:8000/health', timeout=2)" 2>nul
if errorlevel 1 (
    echo APIサーバーが起動していません
    echo APIサーバーを起動してから再実行してください:
    echo   python main.py
    echo または
    echo   docker-compose up -d
    pause
    exit /b 1
)

echo APIサーバーが起動中です
echo.

REM テスト実行
echo テスト実行中...
.venv\Scripts\python.exe test_api.py

REM 結果の確認
if errorlevel 1 (
    echo.
    echo テスト実行中にエラーが発生しました
    pause
    exit /b 1
) else (
    echo.
    echo テスト完了！結果を確認してください：
    echo - 画像: test_output\ フォルダ
    echo - 詳細結果: test_results\ フォルダ
)

REM 元のディレクトリに戻る
cd /d "%CURRENT_DIR%"

echo.
pause