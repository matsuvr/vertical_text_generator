
import os
import requests
import json
import base64
from datetime import datetime

# --- 設定 ---
# APIのベースURL
BASE_URL = "http://localhost:8000"
# 出力先ディレクトリ
OUTPUT_DIR = "operation_checks_output"
# --- 設定ここまで ---

# .env.exampleを参考に環境変数からトークンを取得
API_TOKEN = os.environ.get("API_TOKEN", "")
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_TOKEN}"
}

def save_files(endpoint_name, timestamp, data, suffix=""):
    """レスポンスのJSONと画像を保存する"""
    # ファイル名のサフィックスを組み立て
    filename_suffix = f"_{suffix}" if suffix else ""

    # JSONレスポンスを保存
    json_filename = f"{OUTPUT_DIR}/{endpoint_name}_{timestamp}{filename_suffix}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"   📄 Saved JSON response to {json_filename}")

    # 画像を保存
    if endpoint_name == 'render':
        if "image_base64" in data and data["image_base64"]:
            img_data = base64.b64decode(data["image_base64"])
            img_filename = f"{OUTPUT_DIR}/{endpoint_name}_{timestamp}{filename_suffix}.png"
            with open(img_filename, 'wb') as f:
                f.write(img_data)
            print(f"   🖼️ Saved PNG image to {img_filename}")
    elif endpoint_name == 'batch':
        if "results" in data and isinstance(data["results"], list):
            for i, result in enumerate(data["results"]):
                if "image_base64" in result and result["image_base64"]:
                    img_data = base64.b64decode(result["image_base64"])
                    img_filename = f"{OUTPUT_DIR}/{endpoint_name}_{timestamp}_item_{i+1}.png"
                    with open(img_filename, 'wb') as f:
                        f.write(img_data)
                    print(f"   🖼️ Saved PNG image for item {i+1} to {img_filename}")


def check_render_endpoint(timestamp):
    """/render エンドポイントの動作をチェックします。"""
    print("Checking POST /render endpoint for various fonts...")

    fonts_to_test = [
        ("antique", None),      # APIのデフォルトフォント（アンチック）
        ("gothic", "gothic"),
        ("mincho", "mincho")
    ]

    for font_name_for_file, font_value_for_api in fonts_to_test:
        print(f"  - Testing with font: {font_name_for_file}")
        url = f"{BASE_URL}/render"
        payload = {
            "text": f"これは{font_name_for_file}フォントのテストです。",
            "font_size": 22,
            "padding": 20
        }
        if font_value_for_api:
            payload["font"] = font_value_for_api

        try:
            response = requests.post(url, headers=HEADERS, data=json.dumps(payload))

            if response.status_code == 200:
                try:
                    data = response.json()
                    if "image_base64" in data and data["image_base64"]:
                        print(f"    ✅ /render (font: {font_name_for_file}) returned a successful response.")
                        save_files('render', timestamp, data, suffix=font_name_for_file)
                    else:
                        print(f"    ❌ /render (font: {font_name_for_file}) response is missing 'image_base64'.")
                except json.JSONDecodeError:
                    print(f"    ❌ /render (font: {font_name_for_file}) did not return valid JSON.")
            elif response.status_code == 401:
                 print(f"    ❌ /render (font: {font_name_for_file}) returned 401 Unauthorized. Is the API_TOKEN environment variable set correctly?")
            else:
                print(f"    ❌ /render (font: {font_name_for_file}) failed with status code {response.status_code}.")
                print(f"       Response: {response.text[:200]}...")

        except requests.exceptions.RequestException as e:
            print(f"    ❌ Could not connect to the API at {url}.")
            print(f"       Error: {e}")
            print("       Is the Docker container running?")
            break # APIに接続できない場合はループを中断

def check_batch_render_endpoint(timestamp):
    """/render/batch エンドポイントの動作をチェックします。"""
    print("\nChecking POST /render/batch endpoint...")
    url = f"{BASE_URL}/render/batch"
    payload = {
        "defaults": {"font": "gothic", "font_size": 20},
        "items": [
            {"text": "バッチ処理のテスト１"},
            {"text": "バッチ処理のテスト２", "font": "mincho"}
        ]
    }

    try:
        response = requests.post(url, headers=HEADERS, data=json.dumps(payload))

        if response.status_code == 200:
            try:
                data = response.json()
                if "results" in data and isinstance(data["results"], list) and len(data["results"]) == 2:
                    print("✅ /render/batch endpoint returned a successful response.")
                    save_files('batch', timestamp, data)
                else:
                    print("❌ /render/batch endpoint response is malformed.")
            except json.JSONDecodeError:
                print("❌ /render/batch endpoint did not return valid JSON.")
        elif response.status_code == 401:
             print("❌ /render/batch endpoint returned 401 Unauthorized. Is the API_TOKEN environment variable set correctly?")
        else:
            print(f"❌ /render/batch endpoint failed with status code {response.status_code}.")
            print(f"   Response: {response.text[:200]}...")

    except requests.exceptions.RequestException as e:
        print(f"❌ Could not connect to the API at {url}.")
        print(f"   Error: {e}")


if __name__ == "__main__":
    print("--- API Operation Check Start ---")
    
    # 出力ディレクトリを作成
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 実行日時を取得
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    if not API_TOKEN:
        print("⚠️  Warning: API_TOKEN environment variable is not set. Authentication may fail.")

    check_render_endpoint(timestamp_str)
    check_batch_render_endpoint(timestamp_str)
    
    print("\n--- API Operation Check End ---")
