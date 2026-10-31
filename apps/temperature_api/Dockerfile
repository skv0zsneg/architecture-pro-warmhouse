FROM python:3.12-slim
WORKDIR /app
COPY temperature_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY temperature_api ./temperature_api
EXPOSE 8081
CMD ["uvicorn", "temperature_api.main:app", "--host", "0.0.0.0", "--port", "8081"]
