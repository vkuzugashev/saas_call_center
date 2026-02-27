FROM python:3-alpine

EXPOSE 5000

WORKDIR /app

COPY requirements.txt .
COPY app.py .
COPY create_db.py .
COPY models.py .
COPY pages/ pages/
COPY static/ static/
COPY templates/ templates/

RUN python -m pip install --no-cache-dir -r requirements.txt

CMD [ "python", "-u", "./app.py"]
