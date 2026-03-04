FROM python:3-alpine

COPY app.py .
COPY models/ models/
COPY requirements.txt .

RUN python -m pip install --user --no-cache-dir -r requirements.txt

CMD [ "python", "-u", "./app.py"]