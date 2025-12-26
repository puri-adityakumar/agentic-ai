FROM python:3.13.4-slim-bullseye

RUN apt-get update && apt-get install -y curl

# Create python virtual environment
# isolate our python app and installs from system-level python
RUN python -m venv /opt/venv/
ENV PATH=/opt/venv/bin:$PATH


WORKDIR /app

# COPY local_folder/file container_destination
COPY requirements.txt /tmp/requirements.txt

# RUN within_container_while_building
RUN pip install -r /tmp/requirements.txt

COPY ./src .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]