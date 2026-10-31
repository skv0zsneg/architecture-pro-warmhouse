FROM python:3.12-slim
WORKDIR /app
COPY devices_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY devices_service ./devices_service
EXPOSE 8082
CMD ["uvicorn", "devices_service.main:app", "--host", "0.0.0.0", "--port", "8082"]
