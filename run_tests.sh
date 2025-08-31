#!/bin/bash
# 日本語縦書きAPI テスト実行シェルスクリプト
# 使用方法: ./run_tests.sh

set -e  # エラー時に終了

echo "==================================="
echo "日本語縦書きAPI テスト実行"
echo "==================================="

# スクリプトのディレクトリに移動
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
cd "$SCRIPT_DIR"

# 仮想環境の確認
if [ ! -f ".venv/bin/python" ] && [ ! -f ".venv/Scripts/python.exe" ]; then
    echo "エラー: 仮想環境が見つかりません"
    echo ".venv/bin/python または .venv/Scripts/python.exe が存在することを確認してください"
    exit 1
fi

# Pythonパスを設定
if [ -f ".venv/bin/python" ]; then
    PYTHON_PATH=".venv/bin/python"
else
    PYTHON_PATH=".venv/Scripts/python.exe"
fi

# APIサーバーが起動しているかチェック
echo "APIサーバーの起動状況をチェック中..."
if ! $PYTHON_PATH -c "import requests; requests.get('http://localhost:8000/health', timeout=2)" 2>/dev/null; then
    echo "APIサーバーが起動していません"
    echo "APIサーバーを起動してから再実行してください:"
    echo "  python main.py"
    echo "または"
    echo "  docker-compose up -d"
    exit 1
fi

echo "APIサーバーが起動中です"
echo

# テスト実行
echo "テスト実行中..."
$PYTHON_PATH test_api.py

# 結果の表示
echo
echo "テスト完了！結果を確認してください："
echo "- 画像: test_output/ フォルダ"
echo "- 詳細結果: test_results/ フォルダ"