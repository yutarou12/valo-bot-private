FROM python:3.10-slim-bullseye as builder
WORKDIR /app
COPY requirements.txt .

RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.10-slim-bullseye as runtime
WORKDIR /app

ENV TZ Asia/Tokyo

# builderから必要な内容をコピー
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

ENTRYPOINT ["python", "main.py"]