# Python 3.10ベースのイメージを使用
FROM python:3.10-slim

# 必要なライブラリをインストール
RUN apt-get update && apt-get install -y libexpat1

# 作業ディレクトリを設定
WORKDIR /app

# requirements.txtをコンテナにコピーして依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのコードをコンテナにコピー
COPY . .

# ポート8080を公開
EXPOSE 8080

# Flaskアプリケーションを実行
CMD ["python", "main.py"]
