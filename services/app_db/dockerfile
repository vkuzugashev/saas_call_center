FROM python:3 AS build
WORKDIR /app
COPY requirements.txt .
RUN python -m pip install --user --no-cache-dir -r requirements.txt
FROM python:3-alpine
COPY --from=build /root/.local /root/.local
COPY app_db.py .
COPY model.py .
COPY .env.example .env
CMD [ "python", "-u", "./app_db.py"]