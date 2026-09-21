FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 9292

CMD ["python","mcp_server.py"]