FROM python:3-alpine

WORKDIR /app

COPY requirements.txt .
COPY app.py .

RUN python -m pip install --no-cache-dir -r requirements.txt

CMD [ "python", "-u", "./app.py"]