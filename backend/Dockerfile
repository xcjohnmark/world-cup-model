FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./backend/
RUN pip install -r ./backend/requirements.txt
COPY . ./backend/
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}

