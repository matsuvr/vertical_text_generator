# 日本語縦書きAPI テスト自動化設定

このドキュメントでは、日本語縦書きAPIのテスト自動化について説明します。

## 📋 概要

このプロジェクトには以下の自動テスト機能が実装されています：

1. **手動実行スクリプト** - 開発者による即座のテスト実行
2. **Git Hooks** - コミット前の品質チェック
3. **CI/CD パイプライン** - プッシュ/PR時の自動テスト
4. **定期実行** - スケジュールされた品質監視

## 🚀 手動実行

### Windows環境
```batch
# テスト実行
run_tests.bat

# または、APIサーバーを先に起動してから
python main.py
# 別のコマンドプロンプトで
run_tests.bat
```

### Linux/Mac環境
```bash
# テスト実行
./run_tests.sh

# または、APIサーバーを先に起動してから
python main.py &
./run_tests.sh
```

### 直接実行
```bash
# 仮想環境のPython使用
.venv/Scripts/python test_api.py  # Windows
.venv/bin/python test_api.py      # Linux/Mac

# システムPython使用（非推奨）
python test_api.py
```

## 🔧 Git Hooks設定

### Pre-commit Hook
コミット前に自動的に軽量テストを実行します。

**場所**: `.git/hooks/pre-commit`

**動作**:
- APIサーバーの起動状況を確認
- 起動していれば基本的なAPIテストを実行
- 起動していなければ警告を表示し、ユーザーに選択を求める

**セットアップ**:
```bash
# 自動的に設定済み（実行権限付与済み）
chmod +x .git/hooks/pre-commit
```

## 🌐 CI/CD パイプライン

### GitHub Actions ワークフロー

#### 1. API テスト (`.github/workflows/api-tests.yml`)

**トリガー**:
- `main`, `develop` ブランチへのプッシュ
- 上記ブランチへのプルリクエスト
- 特定ファイル変更時（`main.py`, `test_api.py`, `requirements.txt`）
- 手動実行

**実行内容**:
- Python環境セットアップ
- システム依存関係インストール
- APIサーバー起動
- 完全テストスイート実行
- テスト結果のアーティファクト保存

#### 2. 定期テスト (`.github/workflows/scheduled-tests.yml`)

**トリガー**:
- 毎日午前2時（JST 11時）: 基本テスト
- 毎週月曜午前3時（JST 12時）: 詳細テスト
- 手動実行（テストタイプ選択可能）

**テストタイプ**:
- `basic`: 標準的なAPIテスト
- `full`: ストレステスト含む完全テスト  
- `performance`: パフォーマンステスト拡張版

## 📊 テスト結果の確認

### ローカル実行時
- **生成画像**: `test_output/` フォルダ
- **詳細結果**: `test_results/` フォルダ（JSON形式）
- **コンソール出力**: リアルタイム結果表示

### CI/CD実行時
- **GitHub Actions**: Actions タブで実行結果を確認
- **アーティファクト**: テスト結果ファイルをダウンロード可能
- **サマリー**: 成功率や詳細がStep Summaryに表示

## ⚙️ テスト設定

### 環境変数
```bash
# APIトークン（デフォルト: your-secret-token-here）
export API_TOKEN="your-actual-token-here"

# API URL（デフォルト: http://localhost:8000）
export API_URL="http://your-api-server:8000"
```

### テストケース
テストスクリプトには以下のテストケースが含まれています：

1. **エンドポイントテスト**
   - ヘルスチェック (`/health`)
   - ルートエンドポイント (`/`)
   - デバッグHTML (`/debug/html`)

2. **認証テスト**
   - 認証なしリクエスト
   - 無効なトークン

3. **バリデーションテスト**
   - 空のテキスト
   - 無効なパラメータ（フォントサイズ、行間、フォント名）

4. **レンダリングテスト**
   - 基本的な縦書き
   - 長文テスト
   - 小さなフォントサイズ
   - 特殊文字（罫線、ダッシュ）
   - 異なるフォント（ゴシック、明朝）
   - 縦中横（数字）
   - 省略記号

5. **パフォーマンステスト**
   - 同一リクエストの複数回実行
   - レスポンス時間測定

## 🐛 トラブルシューティング

### よくある問題

#### 1. APIサーバーが起動していない
```
[NG] APIサーバーに接続できません
```

**解決方法**:
```bash
# APIサーバーを起動
python main.py

# または Docker使用
docker-compose up -d
```

#### 2. 依存関係の不足
```
ModuleNotFoundError: No module named 'playwright'
```

**解決方法**:
```bash
# 依存関係を再インストール
pip install -r requirements.txt
playwright install chromium
```

#### 3. フォントファイルが見つからない
```
Font file not found at fonts/GenEiAntiqueNv5-M.ttf
```

**解決方法**:
- `fonts/` ディレクトリにフォントファイルを配置
- システムフォントが自動的に使用される（警告は無視可能）

#### 4. ポート競合
```
Address already in use: 8000
```

**解決方法**:
```bash
# 既存プロセスを確認・停止
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# または別のポートを使用
PORT=8080 python main.py
```

### Git Hooks のトラブル

#### Pre-commit が実行されない
```bash
# 実行権限を確認
ls -la .git/hooks/pre-commit

# 権限がない場合
chmod +x .git/hooks/pre-commit
```

#### Hook を無効にしたい場合
```bash
# 一時的に無効化
git commit --no-verify -m "commit message"

# 完全に無効化
rm .git/hooks/pre-commit
```

## 📈 テスト結果の解釈

### 成功の指標
- **成功率 100%**: 全てのテストケースが成功
- **レスポンス時間 < 5秒**: パフォーマンスが良好
- **画像生成成功**: 全ての画像が正常に生成・保存

### 注意が必要な指標
- **成功率 < 100%**: 一部機能に問題がある可能性
- **レスポンス時間 > 10秒**: パフォーマンス改善が必要
- **バリデーションエラー**: 入力チェックに問題

## 🔧 カスタマイズ

### テストケースの追加
`test_api.py` の `test_cases` リストに新しいテストを追加：

```python
{
    "name": "my_custom_test",
    "data": {
        "text": "カスタムテスト",
        "font_size": 24,
        "font": "gothic"
    }
}
```

### 新しいテスト種類の追加
新しいテスト関数を作成し、`main()` 関数で呼び出し：

```python
def test_my_feature(api_url, token):
    """新機能のテスト"""
    # テストロジックを実装
    pass

def main():
    # 既存のテスト...
    test_my_feature(api_url, token)
```

### CI/CD設定の変更
- **実行頻度**: `.github/workflows/scheduled-tests.yml` の cron 設定を変更
- **テスト環境**: Python バージョンやOS環境を変更
- **通知設定**: 失敗時のSlack通知等を追加

## 📚 参考資料

- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Playwright Python](https://playwright.dev/python/)
- [Git Hooks](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks)

---

**最終更新**: 2025-08-31  
**バージョン**: 1.0.0