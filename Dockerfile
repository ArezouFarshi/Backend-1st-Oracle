# Use Python 3.11 instead of 3.13
FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["python", "app.py"]
