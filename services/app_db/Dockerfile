FROM python:3 AS build

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --user --no-cache-dir -r requirements.txt

FROM python:3-alpine

COPY --from=build /root/.local /root/.local
COPY app.py .
COPY model.py .

CMD [ "python", "-u", "./app.py"]