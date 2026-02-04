FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "src.app:app"]