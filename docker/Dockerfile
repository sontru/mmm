FROM python:3.11-slim
WORKDIR /opt/mmm
COPY . /opt/mmm
ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "-m", "mmm_server.app"]
