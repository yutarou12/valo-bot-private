FROM python:3.10-alpine

WORKDIR /app
COPY requirements.txt /app/requirements.txt

RUN apk -y update && apk -y install  \
    libopencv-dev \
    tesseract-ocr \
    libtesseract-dev \
    && apk clean
RUN python -m pip install --upgrade pip setuptools wheel
RUN if [ -f /app/requirements.txt ]; then python -m pip install -r /app/requirements.txt; fi

ENTRYPOINT ["python", "main.py"]