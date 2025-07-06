FROM python:3.10-buster

WORKDIR /app
COPY requirements.txt /app/requirements.txt

RUN apt -y update && apt -y install  \
    libopencv-dev \
    tesseract-ocr \
    libtesseract-dev \
    && apt clean && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --upgrade pip setuptools wheel
RUN if [ -f /app/requirements.txt ]; then python -m pip install -r /app/requirements.txt; fi

ENTRYPOINT ["python", "main.py"]