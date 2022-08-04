FROM python:3.9-buster
ENV PYTHONUNBUFFERED=1

ENV LANG="ja_JP UTF-8" LANGUAGE="ja_JP:ja" LC_ALL="ja_JP.UTF-8" TZ="Asia/Tokyo"

RUN apt-get update && apt-get install -y ffmpeg libsm6 libxext6 git ninja-build libglib2.0-0 libsm6 libxrender-dev libxext6 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .
CMD ["streamlit", "run", "app.py"]