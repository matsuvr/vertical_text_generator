# 日本語縦書きテキスト画像生成API

HTMLとCSSを使用して日本語の縦書きテキストを画像として生成するAPIです。

## 機能

- HTML/CSSによる安定した日本語縦書きレンダリング
- 透明背景のPNG画像生成
- BudouXによる自然な改行
- 行頭禁則処理（、 。 」 〟 と促音記号の行頭回避）
- 縦組非対応の棒状記号を自動回転し中央揃え

- 自動トリミング（文字列をピッタリ囲む）
- フォント選択機能（Gothic/Mincho、未指定/無効時はアンチック）
- 一括レンダリング対応

## APIエンドポイント

### POST /render

縦書きテキストをレンダリングしてPNG画像を生成します。

#### リクエストパラメータ

| パラメータ         | 型      | 必須 | デフォルト | 説明                                                                                    |
| ------------------ | ------- | ---- | ---------- | --------------------------------------------------------------------------------------- |
| text               | string  | ✓    | -          | レンダリングするテキスト                                                                |
| font               | string  | -    | null       | 使用するフォント（"gothic" または "mincho"。未指定/無効時はアンチックにフォールバック） |
| font_size          | integer | -    | 20         | フォントサイズ (8-100)                                                                  |
| line_height        | float   | -    | 1.6        | 行間 (1.0-3.0)                                                                          |
| letter_spacing     | float   | -    | 0.05       | 文字間（em単位） (0-0.5)                                                                |
| padding            | integer | -    | 20         | 余白（ピクセル） (0-100)                                                                |
| use_tategaki_js    | boolean | -    | false      | Tategaki.jsライブラリを使用                                                             |
| max_chars_per_line | integer | -    | null       | 1行あたりの最大文字数（BudouXで自動改行）                                               |

#### フォントオプション

- `gothic`: ゴシック体（GenEiMGothic2-Regular.ttf）
- `mincho`: 明朝体（GenEiChikugoMin3-R.ttf）
- 指定なし/無効指定: デフォルト（アンチック：GenEiAntiqueNv5-M.ttf）

備考:

- `font` に "gothic"/"mincho" 以外を指定した場合もアンチックにフォールバックします。
- アンチックを明示したい場合は `font` を省略するのが推奨です。

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
  "trimmed": true,
  "font": "mincho"
}
```

フィールド説明:

- `font`: 実際に使用されたフォント名（`antique`/`gothic`/`mincho`）

### POST /render/batch

複数のテキストをまとめてレンダリングしてPNG画像を生成します。

- `items` 配列の最大長は50。超過した場合は400 Bad Requestを返します。
- `defaults` で共通パラメータを指定でき、各アイテムで上書きできます。
- 無効なフォント指定はアンチック体にフォールバックします。
- 各結果オブジェクトに実際に使用された `font` 名が含まれます。

#### リクエスト例

```jsonc
{
  "defaults": { "font": "gothic", "font_size": 20 },
  "items": [
    { "text": "こんにちは世界" },
    { "text": "フォントが存在しない例", "font": "unknown_font" },
  ],
}
```

#### レスポンス例

```jsonc
{
  "results": [
    {
      "image_base64": "...",
      "width": 120,
      "height": 200,
      "processing_time_ms": 456.7,
      "trimmed": false,
      "font": "gothic",
    },
    {
      "image_base64": "...",
      "width": 120,
      "height": 200,
      "processing_time_ms": 789.0,
      "trimmed": true,
      "font": "mincho",
    },
  ],
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
- `POST /render/batch`: 複数テキストをまとめてレンダリング（要認証）

## Docker: ローカル検証手順（gunicorn + uvicorn workers）

変更後にコンテナ内でChromiumが正常に起動するかを確かめるための簡単な手順:

1. イメージをビルド:

```bash
docker build -t vertical-text-generator:local .
```

2. コンテナを起動（ポート8080を公開）:

```bash
docker run --rm -p 8080:8000 --shm-size=1g \
  -e WEB_CONCURRENCY=4 \
  -e PAGE_POOL_SIZE=2 \
  vertical-text-generator:local
```

注意点:

- `--shm-size=1g` を付けると /dev/shm を増やし、Chromiumの共有メモリ不足によるクラッシュを防げます。
- Cloud Run等にデプロイする場合、Dockerfileに必要なライブラリを追加済みなので、そのままデプロイできます。

## 高負荷向けチューニング（起動時プレロード/常駐 + ワーカー）

本リポジトリは以下の通り、フォントとPlaywrightをプロセス生存中ずっとメモリ常駐させ、大量リクエストを高速に捌く構成です。

- フォント: `JapaneseVerticalHTMLGenerator` 初期化時に Base64 エンコードしてメモリキャッシュ（環境変数 `PRELOAD_FONTS=1`）。不足分メモリを先取り確保（`FONT_MEMORY_RESERVE_MB`）。
- ブラウザ: Gunicornワーカー毎にFastAPI `startup`でPlaywrightを起動し、ページプールを用意（`PAGE_POOL_SIZE` はワーカー毎に適用）。
- ページ事前作成: 起動時にプール容量まで `new_page` してキューに投入（`PRECREATE_PAGES=1`）。
- ウォームアップ: 起動直後に軽いレンダリングを1回実行してJITやフォントを温め（`WARMUP_RENDER_ON_STARTUP=1`）。

主要な環境変数（抜粋）:

- `PRELOAD_FONTS`: 起動時にフォントをBase64化して全てメモリキャッシュ（既定: `1`）。
- `FONT_MEMORY_RESERVE_MB`: フォントキャッシュ不足分をゼロ埋めで先取り確保（既定: `128`）。
- `WEB_CONCURRENCY` : Gunicornワーカー数（既定: `4`）。
- `PAGE_POOL_SIZE` : 1ワーカーあたりのPlaywrightページ数（既定: `2`）。
- `PRECREATE_PAGES` : 起動時に `PAGE_POOL_SIZE` 個のページを先に作成（既定: `1`）。
- `WARMUP_RENDER_ON_STARTUP` : 起動時に軽いレンダリングを1回（既定: `1`）。

Gunicorn関連の追加ENV（任意）:

- `GUNICORN_TIMEOUT`（既定: `180`）: リクエストのタイムアウト秒。
- `GUNICORN_GRACEFUL_TIMEOUT`（既定: `30`）: 優雅なシャットダウン待ち秒。
- `GUNICORN_KEEPALIVE`（既定: `5`）: keep-alive秒。
- `GUNICORN_MAX_REQUESTS`（既定: `0` 無効）: メモリリーク対策のワーカー再起動間隔。必要なら `1000` など。

メモ:

- メモリとCPUに余裕がある場合は `WEB_CONCURRENCY` と `PAGE_POOL_SIZE` の積（=総ページ数）を増やすとスループットが上がります。目安: 総ページ <= CPUスレッド数〜2倍。
- 各ワーカーは独立にChromiumを保持します。`WEB_CONCURRENCY` を増やすとブラウザプロセスも増えますが、障害分離・可用性が向上します。
