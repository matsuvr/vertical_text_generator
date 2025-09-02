#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""日本語縦書きAPIのテストスクリプト
使い方: python test_api.py
"""

import base64
import json
import os
import sys
import time
from datetime import datetime

import requests

# Windows環境での文字エンコーディング設定
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer)
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer)


def check_api_status(api_url):
    """APIの状態をチェック"""
    try:
        # ヘルスチェック
        health_response = requests.get(f"{api_url}/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"[OK] APIサーバー起動中: {health_data.get('status', 'unknown')}")
            print(f"  バージョン: {health_data.get('version', 'unknown')}")
            return True
        else:
            print(f"[NG] ヘルスチェック失敗: {health_response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[NG] APIサーバーに接続できません: {e}")
        return False


def test_endpoints(api_url, token):
    """各エンドポイントのテスト"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    print("\n=== エンドポイントテスト ===")

    # ルートエンドポイント
    try:
        response = requests.get(f"{api_url}/")
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] GET /: {data.get('title', 'Unknown')}")
        else:
            print(f"[NG] GET / 失敗: {response.status_code}")
    except Exception as e:
        print(f"[NG] GET / エラー: {e}")

    # デバッグエンドポイント
    try:
        response = requests.get(
            f"{api_url}/debug/html",
            headers=headers,
            params={"text": "デバッグテスト", "font_size": 20},
        )
        if response.status_code == 200:
            print("[OK] GET /debug/html: HTMLレスポンス正常")
        else:
            print(f"[NG] GET /debug/html 失敗: {response.status_code}")
    except Exception as e:
        print(f"[NG] GET /debug/html エラー: {e}")


def test_auth(api_url):
    """認証のテスト"""
    print("\n=== 認証テスト ===")

    # 認証なし
    try:
        response = requests.post(f"{api_url}/render", json={"text": "test"})
        if response.status_code == 401:
            print("[OK] 認証なし: 401 Unauthorized")
        else:
            print(f"[NG] 認証なし: 期待値401, 実際{response.status_code}")
    except Exception as e:
        print(f"[NG] 認証なしテストエラー: {e}")

    # 無効なトークン
    try:
        headers = {"Authorization": "Bearer invalid-token"}
        response = requests.post(
            f"{api_url}/render", headers=headers, json={"text": "test"}
        )
        if response.status_code == 401:
            print("[OK] 無効なトークン: 401 Unauthorized")
        else:
            print(f"[NG] 無効なトークン: 期待値401, 実際{response.status_code}")
    except Exception as e:
        print(f"[NG] 無効なトークンテストエラー: {e}")


def test_validation(api_url, token):
    """バリデーションのテスト"""
    print("\n=== バリデーションテスト ===")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    validation_tests = [
        {"name": "空のテキスト", "data": {"text": ""}, "expected": 422},
        {
            "name": "無効なフォントサイズ",
            "data": {"text": "test", "font_size": 200},
            "expected": 422,
        },
        {
            "name": "無効な行間",
            "data": {"text": "test", "line_height": 5.0},
            "expected": 422,
        },
        {
            "name": "無効なフォント",
            "data": {"text": "test", "font": "invalid"},
            "expected": 422,
        },
    ]

    for test in validation_tests:
        try:
            response = requests.post(
                f"{api_url}/render", headers=headers, json=test["data"]
            )
            if response.status_code == test["expected"]:
                print(f"[OK] {test['name']}: {response.status_code}")
            else:
                print(
                    f"[NG] {test['name']}: 期待値{test['expected']}, 実際{response.status_code}"
                )
        except Exception as e:
            print(f"[NG] {test['name']}エラー: {e}")


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
        "X-Correlation-ID": f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
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
                "text": "吾輩は猫である。名前はまだ無い。どこで生れたかとんと見当がつかぬ。何でも薄暗いじめじめした所でニャーニャー泣いていた事だけは記憶している。",
                "font_size": 20,
                "max_chars_per_line": 15,
            },
        },
        {
            "name": "small_font",
            "data": {
                "text": "小さい文字\nテスト\n複数行",
                "font_size": 12,
                "max_chars_per_line": 8,
            },
        },
        {
            "name": "dashes",
            "data": {
                # 含まれる記号: U+2015(―)×2, U+2014(—)×2, U+2500(─)×2
                "text": "これは――テスト——です。次の行は──罫線──の確認。",
                "font_size": 24,
                "max_chars_per_line": 12,
            },
        },
        {
            "name": "font_gothic",
            "data": {
                "text": "ゴシック体\nテストです",
                "font": "gothic",
                "font_size": 20,
            },
        },
        {
            "name": "font_mincho",
            "data": {
                "text": "明朝体\nテストです",
                "font": "mincho",
                "font_size": 20,
            },
        },
        {
            "name": "numbers_tcy",
            "data": {
                "text": "平成30年12月25日\n令和2年3月14日\n西暦2024年",
                "font_size": 18,
                "max_chars_per_line": 8,
            },
        },
        {
            "name": "ellipsis_test",
            "data": {
                "text": "省略記号…の\nテストです…",
                "font_size": 20,
            },
        },
    ]

    # 結果保存用ディレクトリ
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)

    # テスト結果保存用ディレクトリ
    results_dir = "test_results"
    os.makedirs(results_dir, exist_ok=True)

    print("\n=== レンダリングテスト ===")
    print(f"APIテスト開始: {api_url}")
    print(f"出力ディレクトリ: {output_dir}")
    print("-" * 50)

    test_results = []
    success_count = 0

    for test in test_cases:
        print(f"\nテスト: {test['name']}")
        print(f"リクエスト: {json.dumps(test['data'], ensure_ascii=False, indent=2)}")

        test_start_time = time.time()

        try:
            # APIリクエスト
            response = requests.post(
                f"{api_url}/render", headers=headers, json=test["data"], timeout=30
            )

            if response.status_code == 200:
                # 成功
                result = response.json()

                # 画像をデコードして保存
                image_data = base64.b64decode(result["image_base64"])
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{output_dir}/{test['name']}_{timestamp}.png"

                with open(filename, "wb") as f:
                    f.write(image_data)

                test_time = time.time() - test_start_time

                print(f"[OK] 成功: {filename}")
                print(f"  サイズ: {result['width']}x{result['height']} px")
                print(f"  処理時間: {result['processing_time_ms']:.2f} ms")
                print(f"  テスト時間: {test_time:.2f} s")
                print(
                    f"  トリミング: {'はい' if result.get('trimmed', False) else 'いいえ'}"
                )

                # 相関IDの確認
                correlation_id = response.headers.get("X-Correlation-ID")
                if correlation_id:
                    print(f"  相関ID: {correlation_id}")

                test_results.append(
                    {
                        "name": test["name"],
                        "status": "success",
                        "processing_time_ms": result["processing_time_ms"],
                        "test_time_s": test_time,
                        "width": result["width"],
                        "height": result["height"],
                        "trimmed": result.get("trimmed", False),
                        "filename": filename,
                    }
                )
                success_count += 1

            else:
                # エラー
                test_time = time.time() - test_start_time
                print(f"[NG] エラー: {response.status_code}")
                print(f"  詳細: {response.text}")
                print(f"  テスト時間: {test_time:.2f} s")

                test_results.append(
                    {
                        "name": test["name"],
                        "status": "error",
                        "status_code": response.status_code,
                        "test_time_s": test_time,
                        "error": response.text,
                    }
                )

        except Exception as e:
            test_time = time.time() - test_start_time
            print(f"[NG] 例外: {type(e).__name__}: {e}")
            print(f"  テスト時間: {test_time:.2f} s")

            test_results.append(
                {
                    "name": test["name"],
                    "status": "exception",
                    "test_time_s": test_time,
                    "exception": f"{type(e).__name__}: {e}",
                }
            )

    # テスト結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    print(f"総テスト数: {len(test_cases)}")
    print(f"成功: {success_count}")
    print(f"失敗: {len(test_cases) - success_count}")
    print(f"成功率: {success_count / len(test_cases) * 100:.1f}%")

    # テスト結果をJSONで保存
    result_file = (
        f"{results_dir}/test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "api_url": api_url,
                "total_tests": len(test_cases),
                "success_count": success_count,
                "success_rate": success_count / len(test_cases) * 100,
                "results": test_results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\n詳細結果: {result_file}")
    print("テスト完了")


def run_performance_test(api_url, token, num_requests=5):
    """パフォーマンステスト"""
    print("\n=== パフォーマンステスト ===")
    print(f"同一リクエストを{num_requests}回実行")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    test_data = {
        "text": "パフォーマンステスト用のテキストです。\n複数行のテストを行います。",
        "font_size": 20,
        "max_chars_per_line": 15,
    }

    times = []
    processing_times = []

    for i in range(num_requests):
        print(f"  リクエスト {i + 1}/{num_requests}...", end=" ")

        start_time = time.time()
        try:
            response = requests.post(
                f"{api_url}/render", headers=headers, json=test_data, timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                total_time = time.time() - start_time
                times.append(total_time)
                processing_times.append(result["processing_time_ms"])
                print(
                    f"[OK] {total_time:.2f}s (処理: {result['processing_time_ms']:.2f}ms)"
                )
            else:
                print(f"[NG] エラー: {response.status_code}")
        except Exception as e:
            print(f"[NG] 例外: {e}")

    if times:
        print("\nパフォーマンス結果:")
        print(
            f"  総時間 - 平均: {sum(times) / len(times):.2f}s, 最小: {min(times):.2f}s, 最大: {max(times):.2f}s"
        )
        print(
            f"  処理時間 - 平均: {sum(processing_times) / len(processing_times):.2f}ms, 最小: {min(processing_times):.2f}ms, 最大: {max(processing_times):.2f}ms"
        )


def main():
    """メイン関数"""
    api_url = "http://localhost:8000"

    # コマンドライン引数からトークンを取得（オプション）
    token = sys.argv[1] if len(sys.argv) > 1 else None
    if not token:
        token = os.getenv("API_TOKEN", "your-secret-token-here")

    print("=== 日本語縦書きAPI 統合テスト ===")
    print(f"API URL: {api_url}")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # APIの状態チェック
    if not check_api_status(api_url):
        print("\nAPIサーバーが起動していません")
        print("以下のいずれかを実行してAPIサーバーを起動してください:")
        print("  1. docker-compose up -d")
        print("  2. python main.py")
        sys.exit(1)

    # 各種テストを実行
    test_endpoints(api_url, token)
    test_auth(api_url)
    test_validation(api_url, token)
    test_api(api_url, token)
    run_performance_test(api_url, token)

    print("\n" + "=" * 60)
    print("全テスト完了")
    print("=" * 60)


if __name__ == "__main__":
    main()
