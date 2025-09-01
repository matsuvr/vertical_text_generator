# 日本語縦書きテキスト画像生成API

HTMLとCSSを使用して日本語の縦書きテキストを画像として生成するAPIです。

## 機能

- HTML/CSSによる安定した日本語縦書きレンダリング
- 透明背景のPNG画像生成
- BudouXによる自然な改行
- 自動トリミング（文字列をピッタリ囲む）
- フォント選択機能（Gothic/Mincho）

## APIエンドポイント

### POST /render

縦書きテキストをレンダリングしてPNG画像を生成します。

#### リクエストパラメータ

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|-----------|---|------|-----------|------|
| text | string | ✓ | - | レンダリングするテキスト |
| font | string | - | null | 使用するフォント ("gothic" または "mincho") |
| font_size | integer | - | 20 | フォントサイズ (8-100) |
| line_height | float | - | 1.6 | 行間 (1.0-3.0) |
| letter_spacing | float | - | 0.05 | 文字間（em単位） (0-0.5) |
| padding | integer | - | 20 | 余白（ピクセル） (0-100) |
| use_tategaki_js | boolean | - | false | Tategaki.jsライブラリを使用 |
| max_chars_per_line | integer | - | null | 1行あたりの最大文字数（BudouXで自動改行） |

#### フォントオプション

- `gothic`: ゴシック体（GenEiMGothic2-Regular.ttf）
- `mincho`: 明朝体（GenEiChikugoMin3-R.ttf）
- 指定なし: デフォルトフォント（GenEiAntiqueNv5-M.ttf）

#### リクエスト例

```json
{
  "text": "吾輩は猫である。\n名前はまだ無い。",
  "font": "mincho",
  "font_size": 24,
  "line_height": 1.8,
  "letter_spacing": 0.1,
  "padding": 30
}
```

#### レスポンス

```json
{
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAAA...",
  "width": 400,
  "height": 600,
  "processing_time_ms": 1234.5,
  "trimmed": true
}
```

## 認証

保護されたエンドポイントにアクセスするには、Bearerトークンが必要です。

```
Authorization: Bearer your-secret-token-here
```

## その他のエンドポイント

- `GET /`: APIの基本情報（認証不要）
- `GET /health`: ヘルスチェック（認証不要）
- `GET /debug/html`: 生成されるHTMLを確認（要認証）

## Docker: ローカル検証手順

変更後にコンテナ内でChromiumが正常に起動するかを確かめるための簡単な手順:

1. イメージをビルド:

```bash
docker build -t vertical-text-generator:local .
```

2. コンテナを起動（ポート8080を公開）:

```bash
docker run --rm -p 8080:8080 --shm-size=1g vertical-text-generator:local
```

注意点:
- `--shm-size=1g` を付けると /dev/shm を増やし、Chromiumの共有メモリ不足によるクラッシュを防げます。
- Cloud Run等にデプロイする場合、Dockerfileに必要なライブラリを追加済みなので、そのままデプロイできます。
