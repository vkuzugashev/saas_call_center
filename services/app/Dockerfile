FROM python:3-alpine

EXPOSE 5000

WORKDIR /app

COPY app.py .
COPY models/ models/
COPY pages/ pages/
COPY static/ static/
COPY templates/ templates/
COPY requirements.txt .

RUN python -m pip install --user --no-cache-dir -r requirements.txt

CMD [ "python", "-u", "./app.py"]
