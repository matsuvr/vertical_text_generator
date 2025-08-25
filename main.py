"""HTMLベース日本語縦書きAPI - Playwrightで高品質な縦書きレンダリング"""

import base64
import io
import logging
import os
import re
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import budoux
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from PIL import Image
from pydantic import BaseModel, Field, validator
from starlette.exceptions import HTTPException as StarletteHTTPException

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HTMLベース日本語縦書きAPI")

# セキュリティ設定 (Authorization欠如も401に統一するため auto_error=False)
security = HTTPBearer(auto_error=False)

# 環境変数からトークンを取得 (デフォルト値を設定)
API_TOKEN = os.getenv("API_TOKEN", "your-secret-token-here")


class ErrorResponse(BaseModel):
    """統一エラーレスポンス"""

    code: str = Field(..., description="アプリケーションエラーコード")
    message: str = Field(..., description="エラーメッセージ（汎用）")
    correlation_id: str = Field(..., alias="correlationId", description="相関ID")
    errors: Optional[list] = Field(default=None, description="詳細エラー（任意）")


def _get_correlation_id(request: Request) -> str:
    """ヘッダから相関IDを取得。無ければ生成。"""
    return (
        request.headers.get("X-Correlation-ID")
        or request.headers.get("X-Correlation-Id")
        or uuid.uuid4().hex
    )


def _error_json_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    errors: Optional[list] = None,
    extra_headers: Optional[dict] = None,
):
    """統一形式のエラーレスポンスを返す（X-Correlation-ID付き）。"""
    cid = _get_correlation_id(request)
    body = ErrorResponse(code=code, message=message, correlationId=cid, errors=errors)
    headers = {"X-Correlation-ID": cid}
    if extra_headers:
        headers.update(extra_headers)
    return JSONResponse(
        status_code=status_code, content=body.model_dump(by_alias=True), headers=headers
    )


def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """Bearerトークンの検証（欠如/不一致ともに401へ統一）"""
    if not credentials or not credentials.credentials:
        # 認証情報欠如 → 401
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if credentials.credentials != API_TOKEN:
        # トークン不一致 → 401
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """バリデーションエラー → 422（統一スキーマ）"""
    cid = _get_correlation_id(request)
    try:
        body = await request.body()
    except Exception:
        body = b""
    logger.error(
        "[VALIDATION_ERROR] Validation failed",
        extra={
            "cid": cid,
            "path": str(request.url),
            "errors": exc.errors(),
            "body": body.decode("utf-8", errors="ignore"),
        },
    )
    headers = {"X-Correlation-ID": cid}
    payload = ErrorResponse(
        code="VALIDATION_ERROR",
        message="Validation failed",
        correlationId=cid,
        errors=exc.errors(),
    )
    return JSONResponse(
        status_code=422, content=payload.model_dump(by_alias=True), headers=headers
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP例外 → 統一スキーマに変換"""
    cid = _get_correlation_id(request)
    status = exc.status_code
    # よく使うコードの標準化
    code_map = {
        401: ("UNAUTHORIZED", "Unauthorized"),
        403: ("FORBIDDEN", "Forbidden"),
        404: ("NOT_FOUND", "Not Found"),
        405: ("METHOD_NOT_ALLOWED", "Method Not Allowed"),
        500: ("INTERNAL_ERROR", "Internal server error"),
    }
    code, message = code_map.get(status, ("HTTP_ERROR", "HTTP error"))

    # ログ(詳細はログにのみ)
    logger.error(
        f"[{code}] {message}",
        extra={
            "cid": cid,
            "path": str(request.url),
            "status": status,
            "detail": str(exc.detail),
        },
    )

    headers = {"X-Correlation-ID": cid}
    # 401はWWW-Authenticateヘッダを付与
    if status == 401:
        headers["WWW-Authenticate"] = "Bearer"
    # 既存ヘッダをマージ
    if exc.headers:
        headers.update(exc.headers)

    payload = ErrorResponse(code=code, message=message, correlationId=cid)
    return JSONResponse(
        status_code=status, content=payload.model_dump(by_alias=True), headers=headers
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """想定外の例外 → 500 統一スキーマ"""
    cid = _get_correlation_id(request)
    logger.error(
        "[INTERNAL_ERROR] Unhandled exception",
        exc_info=True,
        extra={"cid": cid, "path": str(request.url)},
    )
    payload = ErrorResponse(
        code="INTERNAL_ERROR", message="Internal server error", correlationId=cid
    )
    return JSONResponse(
        status_code=500,
        content=payload.model_dump(by_alias=True),
        headers={"X-Correlation-ID": cid},
    )


# リクエストモデル
class VerticalTextRequest(BaseModel):
    text: str = Field(..., description="レンダリングするテキスト")
    font_size: int = Field(default=20, ge=8, le=100, description="フォントサイズ")
    line_height: float = Field(default=1.6, ge=1.0, le=3.0, description="行間")
    letter_spacing: float = Field(
        default=0.05,
        ge=0,
        le=0.5,
        description="文字間（em単位）",
    )
    padding: int = Field(default=20, ge=0, le=100, description="余白（ピクセル）")
    use_tategaki_js: bool = Field(
        default=False,
        description="Tategaki.jsライブラリを使用",
    )
    max_chars_per_line: Optional[int] = Field(
        default=None,
        ge=1,
        le=100,
        description="1行あたりの最大文字数（BudouXで自動改行）",
    )

    @validator("text")
    def text_not_empty(cls, v):
        if not v.strip():
            raise ValueError("テキストが空です")
        return v


# レスポンスモデル
class VerticalTextResponse(BaseModel):
    image_base64: str = Field(..., description="Base64エンコードされた画像")
    width: int = Field(..., description="画像の幅")
    height: int = Field(..., description="画像の高さ")
    processing_time_ms: float = Field(..., description="処理時間（ミリ秒）")
    trimmed: bool = Field(..., description="画像がトリミングされたかどうか")


class JapaneseVerticalHTMLGenerator:
    """HTMLとCSSで日本語縦書きを生成するクラス"""

    def __init__(self, font_path: Optional[str] = None):
        self.font_path = font_path or self._get_default_font_path()
        # BudouXパーサーの初期化
        self.budoux_parser = budoux.load_default_japanese_parser()

    def _get_default_font_path(self) -> str:
        """デフォルトフォントパスを取得"""
        for path in FONT_CANDIDATES:
            if path.exists():
                logger.info(f"Using font: {path}")
                return str(path)

        logger.warning("No Japanese font found, using system default")
        return ""

    def _apply_budoux_line_breaks(self, text: str, max_chars_per_line: int) -> str:
        """BudouXを使用して適切な位置で改行を入れる"""
        lines = text.split("\n")
        processed_lines = []

        for line in lines:
            if len(line) <= max_chars_per_line:
                # 行が最大文字数以下ならそのまま
                processed_lines.append(line)
            else:
                # BudouXで文節に分割
                chunks = self.budoux_parser.parse(line)

                # 文節を組み合わせて行を作成
                current_line = ""
                current_length = 0

                for chunk in chunks:
                    chunk_length = len(chunk)

                    if current_length + chunk_length <= max_chars_per_line:
                        # 現在の行に追加
                        current_line += chunk
                        current_length += chunk_length
                    else:
                        # 新しい行を開始
                        if current_line:
                            processed_lines.append(current_line)
                        current_line = chunk
                        current_length = chunk_length

                # 最後の行を追加
                if current_line:
                    processed_lines.append(current_line)

        return "\n".join(processed_lines)

    def _encode_font_as_base64(self) -> Optional[str]:
        """フォントファイルをBase64エンコード"""
        if not self.font_path or not os.path.exists(self.font_path):
            return None

        try:
            with open(self.font_path, "rb") as f:
                font_data = f.read()
            return base64.b64encode(font_data).decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to encode font: {e}")
            return None

    def _escape_html(self, text: str) -> str:
        """HTMLエスケープ処理"""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

    def _process_text_for_vertical(self, text: str) -> str:
        """縦書き用のテキスト処理（縦中横など）"""
        # 改行を<br>に変換
        text = self._escape_html(text)
        lines = text.split("\n")

        processed_lines = []
        for line in lines:
            # 2桁数字を縦中横にする（3桁以上は除外）
            # 数字の前後が数字でない2桁の数字のみを縦中横にする
            line = re.sub(
                r"(?<!\d)(\d{1,2})(?!\d)",
                r'<span class="tcy">\1</span>',
                line,
            )

            # 三点リーダーを縦書き用の文字に置換（源暎アンチック対応）
            # U+2026（…）をU+FE19（︙）に変換
            line = line.replace("…", "︙")

            processed_lines.append(line)

        return "<br>".join(processed_lines)

    def _calculate_canvas_size(
        self,
        text: str,
        font_size: int,
        line_height: float,
        padding: int,
    ) -> Tuple[int, int]:
        """テキストからキャンバスサイズを推定"""
        lines = text.split("\n")
        max_line_chars = max(len(line) for line in lines) if lines else 0
        num_lines = len(lines)

        column_width = int(font_size * line_height * 1.2)
        estimated_height = int(
            (max_line_chars * font_size * line_height) + (padding * 2) + 50
        )

        chars_per_column = max(10, int(estimated_height / (font_size * line_height)))
        total_chars = sum(len(line) for line in lines)
        estimated_columns = max(
            1, (total_chars + num_lines - 1) // chars_per_column + 1
        )

        estimated_width = (estimated_columns * column_width) + (padding * 2)
        return max(200, estimated_width), max(200, estimated_height)

    def _font_face_css(self, font_base64: Optional[str]) -> str:
        """フォント定義のCSSを生成"""
        if not font_base64:
            return ""
        return f"""
            @font-face {{
                font-family: 'GenEiAntique';
                src: url(data:font/ttf;base64,{font_base64}) format('truetype');
                font-display: block;
            }}
            """

    def create_vertical_html(
        self,
        text: str,
        font_size: int = 20,
        line_height: float = 1.6,
        letter_spacing: float = 0.05,
        padding: int = 20,
        use_tategaki_js: bool = False,
        max_chars_per_line: Optional[int] = None,
    ) -> str:
        """縦書きHTMLを生成"""
        # BudouXによる自動改行処理
        if max_chars_per_line is not None:
            text = self._apply_budoux_line_breaks(text, max_chars_per_line)

        # フォントのBase64エンコード
        font_base64 = self._encode_font_as_base64()

        # テキスト処理
        processed_text = self._process_text_for_vertical(text)

        # テキストの文字数を基に適切なサイズを計算
        lines = text.split("\n")
        max_line_chars = max(len(line) for line in lines) if lines else 0
        num_lines = len(lines)

        # 基本的な幅の計算（1列あたりの幅）
        column_width = int(font_size * line_height * 1.2)  # 1文字の幅 + 余裕

        # 高さの計算（最長行を基準に）
        estimated_height = int(
            (max_line_chars * font_size * line_height) + (padding * 2) + 50,
        )

        # 幅の計算（行数を考慮）
        # 1列に収まる文字数を計算
        chars_per_column = max(10, int(estimated_height / (font_size * line_height)))

        # 必要な列数を計算
        total_chars = sum(len(line) for line in lines)
        estimated_columns = max(
            1,
            (total_chars + num_lines - 1) // chars_per_column + 1,
        )

        # 最終的な幅（複数列の場合）
        estimated_width = (estimated_columns * column_width) + (padding * 2)

        # 最小幅を保証
        estimated_width = max(200, estimated_width)
        estimated_height = max(200, estimated_height)

        # フォントフェイス定義
        font_face = self._font_face_css(font_base64)

        # Tategaki.jsの追加
        tategaki_imports = ""
        tategaki_script = ""
        if use_tategaki_js:
            tategaki_imports = """
            <link rel="stylesheet" href="https://unpkg.com/tategaki/assets/tategaki.css">
            <script src="https://unpkg.com/tategaki/dist/tategaki.min.js"></script>
            """
            tategaki_script = """
            <script>
                // Tategaki.jsの初期化
                document.addEventListener('DOMContentLoaded', function() {
                    new Tategaki('.vertical-text-content');
                });
            </script>
            """

        # HTML生成
        html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {tategaki_imports}
    <style>
        {font_face}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            width: {estimated_width}px;
            height: {estimated_height}px;
            background: transparent;
            overflow: hidden;
        }}

        .vertical-text-container {{
            width: 100%;
            height: 100%;
            padding: {padding}px;
            background: transparent;
        }}

        .vertical-text-content {{
            writing-mode: vertical-rl;
            text-orientation: mixed;
            font-family: 'GenEiAntique', 'Noto Sans CJK JP', 'Hiragino Kaku Gothic ProN', 'Yu Gothic', sans-serif;
            font-size: {font_size}px;
            line-height: {line_height};
            letter-spacing: {letter_spacing}em;
            font-feature-settings: 'vert' 1, 'vrt2' 1, 'vkrn' 1, 'vpal' 1;
            height: 100%;
            width: 100%;
            color: #000;
            overflow: visible;
            word-break: normal;
            text-align: start;
        }}

        /* 縦中横（tate-chu-yoko） */
        .tcy {{
            text-combine-upright: all;
            -webkit-text-combine: horizontal;
            -ms-text-combine-horizontal: all;
            text-orientation: upright;
            display: inline-block;
            vertical-align: middle;
            margin-top: -0.1em;
        }}

        /* ブラウザのデフォルトスタイルを確実にリセット */
        br {{
            margin: 0;
            padding: 0;
            line-height: inherit;
        }}

        /* ルビ対応 */
        ruby {{
            ruby-position: inter-character;
        }}

        rt {{
            font-size: 0.5em;
        }}
    </style>
</head>
<body>
    <div class="vertical-text-container">
        <div class="vertical-text-content">
            {processed_text}
        </div>
    </div>
    {tategaki_script}
</body>
</html>
        """

        return html_content


class HTMLToPNGConverter:
    """HTMLからPNGへの変換クラス（Playwright使用）"""

    @staticmethod
    async def convert_with_playwright(
        html_content: str,
        output_path: str,
    ) -> Tuple[float, int, int]:
        """PlaywrightでHTMLをPNGに変換"""
        start_time = time.time()

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                # Chromiumブラウザを起動
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--font-render-hinting=none",
                        "--disable-font-subpixel-positioning",
                    ],
                )

                try:
                    # ページを作成
                    page = await browser.new_page()

                    # HTMLコンテンツを設定
                    await page.set_content(html_content, wait_until="domcontentloaded")

                    # フォントの読み込み完了を待つ
                    await page.wait_for_function("() => document.fonts.ready")

                    # ページの背景を確実に透明にする
                    await page.evaluate("""
                        () => {
                            document.body.style.backgroundColor = 'transparent';
                            document.documentElement.style.backgroundColor = 'transparent';
                            // すべての要素の背景を透明に
                            const elements = document.querySelectorAll('*');
                            elements.forEach(el => {
                                const computed = window.getComputedStyle(el);
                                if (computed.backgroundColor !== 'rgba(0, 0, 0, 0)' &&
                                    computed.backgroundColor !== 'transparent') {
                                    el.style.backgroundColor = 'transparent';
                                }
                            });
                        }
                    """)

                    # レイアウトの安定化を待つ
                    await page.wait_for_timeout(500)

                    # スクリーンショットを撮影
                    await page.screenshot(
                        path=output_path,
                        full_page=True,
                        type="png",
                        omit_background=True,
                    )

                    # 実際のコンテンツサイズを取得
                    dimensions = await page.evaluate("""
                        () => {
                            const container = document.querySelector('.vertical-text-container');
                            return {
                                width: container.scrollWidth,
                                height: container.scrollHeight
                            };
                        }
                    """)

                    actual_width = dimensions["width"]
                    actual_height = dimensions["height"]

                finally:
                    await browser.close()

        except Exception as e:
            logger.error(f"Playwright conversion failed: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            raise

        return (time.time() - start_time) * 1000, actual_width, actual_height


def trim_image(image_path: str) -> Tuple[Image.Image, bool]:
    """画像の余白をトリミング（文字列をピッタリ囲む）"""
    try:
        img = Image.open(image_path)

        # 既にRGBAの場合はそのまま使用
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        # 画像の境界ボックスを取得（非透明部分）
        bbox = img.getbbox()

        if bbox:
            # 余白なしでピッタリトリミング
            x1, y1, x2, y2 = bbox

            # トリミング
            trimmed = img.crop((x1, y1, x2, y2))
            return trimmed, True

        # トリミングの必要なし
        return img, False

    except Exception as e:
        logger.error(f"Failed to trim image: {e}")
        raise


# グローバルインスタンス
html_generator = JapaneseVerticalHTMLGenerator()
converter = HTMLToPNGConverter()


@app.post(
    "/render",
    response_model=VerticalTextResponse,
    dependencies=[Depends(verify_token)],
)
async def render_vertical_text(request: VerticalTextRequest):
    """縦書きテキストをレンダリング（認証必須）"""
    try:
        # HTML生成
        html_content = html_generator.create_vertical_html(
            text=request.text,
            font_size=request.font_size,
            line_height=request.line_height,
            letter_spacing=request.letter_spacing,
            padding=request.padding,
            use_tategaki_js=request.use_tategaki_js,
            max_chars_per_line=request.max_chars_per_line,
        )

        # 一時ファイルパス
        temp_png = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        temp_png_path = temp_png.name
        temp_png.close()

        # Playwrightで変換実行
        (
            processing_time,
            actual_width,
            actual_height,
        ) = await converter.convert_with_playwright(
            html_content,
            temp_png_path,
        )

        # 画像のトリミング処理
        img, trimmed = trim_image(temp_png_path)

        # トリミングされた画像をバイトデータとして保存
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="PNG", optimize=True)
        image_data = img_byte_arr.getvalue()

        width, height = img.size

        # Base64エンコード
        image_base64 = base64.b64encode(image_data).decode("utf-8")

        # 一時ファイルを削除
        os.unlink(temp_png_path)

        return VerticalTextResponse(
            image_base64=image_base64,
            width=width,
            height=height,
            processing_time_ms=processing_time,
            trimmed=trimmed,
        )

    except Exception:
        # 内部詳細はレスポンスに出さず、ログのみに残す
        logger.error("[INTERNAL_ERROR] Rendering failed", exc_info=True)
        # FastAPIのグローバルハンドラに任せず、明示的に統一スキーマで返す
        # リクエストオブジェクトを取得するために関数シグネチャ変更を避け、Starletteのコンテキストがないため
        # ここでは汎用の相関ID生成のみ行う
        # ただしRequestにアクセスできないため、グローバルハンドラを使うのが安全
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/")
async def root():
    """APIの基本情報（認証不要）"""
    return {
        "title": "HTMLベース日本語縦書きAPI",
        "version": "6.0.0",
        "description": "HTML/CSSによる安定した日本語縦書きレンダリング",
        "features": {
            "html_css": "writing-mode: vertical-rl, text-orientation: mixed",
            "font": "源暎アンチックフォント対応",
            "auto_sizing": "テキスト量に応じた自動サイズ調整",
            "auto_trim": "文字列をピッタリ囲むトリミング",
            "tategaki_js": "Tategaki.jsライブラリ対応（オプション）",
            "transparent_bg": "透明背景対応",
            "converter": "Playwright (Chrome Headless)",
            "budoux": "BudouXによる自然な改行",
        },
        "endpoints": {
            "/render": "縦書きテキストをレンダリング（要認証）",
            "/debug/html": "生成されるHTMLを確認（要認証）",
            "/health": "ヘルスチェック（認証不要）",
        },
        "authentication": "Bearer token required for protected endpoints",
    }


@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "html_generator": "JapaneseVerticalHTMLGenerator",
        "version": "6.0.0",
    }


@app.get("/debug/html", dependencies=[Depends(verify_token)])
async def debug_html(
    text: str = "テスト文字列\n縦書きのテストです。",
    font_size: int = 20,
    use_tategaki_js: bool = False,
    max_chars_per_line: Optional[int] = None,
):
    """生成されるHTMLをデバッグ用に確認（認証必須）"""
    try:
        html_content = html_generator.create_vertical_html(
            text=text,
            font_size=font_size,
            use_tategaki_js=use_tategaki_js,
            max_chars_per_line=max_chars_per_line,
        )
        return HTMLResponse(content=html_content)
    except Exception:
        logger.error("[INTERNAL_ERROR] debug_html failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn

    # Cloud RunではPORT環境変数を使用
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
