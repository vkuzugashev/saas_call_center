FROM python:3-alpine

EXPOSE 5078

WORKDIR /app

COPY requirements.txt .
COPY app.py .
COPY model.py .

RUN python -m pip install --no-cache-dir -r requirements.txt

CMD [ "python", "-u", "./app.py"]