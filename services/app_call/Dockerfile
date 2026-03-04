FROM python:3-alpine

WORKDIR /app

COPY app.py .
COPY requirements.txt .

RUN python -m pip install --no-cache-dir -r requirements.txt

CMD [ "python", "-u", "./app.py"]