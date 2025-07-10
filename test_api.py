#!/usr/bin/env python3
"""日本語縦書きAPIのテストスクリプト
使い方: python test_api.py
"""

import base64
import json
import os
import sys
from datetime import datetime

import requests


def test_api(api_url="http://localhost:8000", token=None):
    """APIをテストして画像を保存"""
    # トークンの取得
    if not token:
        token = os.getenv(
            "API_TOKEN",
            "your-secret-token-here",
        )

    # ヘッダー
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # テストケース
    test_cases = [
        {
            "name": "basic",
            "data": {
                "text": "こんにちは、世界！\n日本語の縦書きです。",
                "font_size": 24,
                "max_chars_per_line": 10,
            },
        },
        {
            "name": "long_text",
            "data": {
                "text": "吾輩は猫である。名前はまだ無い。どこで生れたかとんと見当がつかぬ。",
                "font_size": 20,
                "max_chars_per_line": 10,
            },
        },
        {
            "name": "small_font",
            "data": {
                "text": "小さい文字\nテスト",
                "font_size": 12,
            },
        },
    ]

    # 結果保存用ディレクトリ
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)

    print(f"APIテスト開始: {api_url}")
    print(f"出力ディレクトリ: {output_dir}")
    print("-" * 50)

    for test in test_cases:
        print(f"\nテスト: {test['name']}")
        print(f"リクエスト: {json.dumps(test['data'], ensure_ascii=False)}")

        try:
            # APIリクエスト
            response = requests.post(
                f"{api_url}/render",
                headers=headers,
                json=test["data"],
            )

            if response.status_code == 200:
                # 成功
                result = response.json()

                # 画像をデコードして保存
                image_data = base64.b64decode(result["image_base64"])
                filename = f"{output_dir}/{test['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

                with open(filename, "wb") as f:
                    f.write(image_data)

                print(f"✓ 成功: {filename}")
                print(f"  サイズ: {result['width']}x{result['height']} px")
                print(f"  処理時間: {result['processing_time_ms']:.2f} ms")

            else:
                # エラー
                print(f"✗ エラー: {response.status_code}")
                print(f"  詳細: {response.text}")

        except Exception as e:
            print(f"✗ 例外: {type(e).__name__}: {e}")

    print("\n" + "-" * 50)
    print("テスト完了")


def main():
    """メイン関数"""
    # コマンドライン引数からトークンを取得（オプション）
    token = sys.argv[1] if len(sys.argv) > 1 else None

    # ヘルスチェック
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code != 200:
            print("APIサーバーが起動していません")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print("APIサーバーに接続できません")
        print("docker-compose up -d を実行してください")
        sys.exit(1)

    # テスト実行
    test_api(token=token)


if __name__ == "__main__":
    main()
