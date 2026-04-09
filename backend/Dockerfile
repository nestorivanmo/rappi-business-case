FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Shell form so ${PORT} is expanded at runtime. Railway sets PORT; locally defaults to 8000.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
