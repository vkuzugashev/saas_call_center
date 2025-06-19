FROM python:3-alpine
EXPOSE 5078
WORKDIR /app
COPY requirements.txt .
COPY app_new_call.py .
COPY .env.example .env
RUN python -m pip install --no-cache-dir -r requirements.txt
CMD [ "python", "-u", "./app_new_call.py"]