# Pythonベースのイメージを使用
FROM python:3.10-slim

# 作業ディレクトリを作成
WORKDIR /app

# 必要なパッケージをインストール
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# Gunicornの設定で、タイムアウトとワーカー数を指定
CMD ["gunicorn", "-b", ":8080", "--timeout", "120", "--workers", "2", "main:app"]
