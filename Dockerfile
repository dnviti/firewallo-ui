FROM python:3.13

RUN apt-get update && \
    apt-get install -y wireguard-tools && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app
COPY requirements.txt .
COPY app/ ./

RUN rm -rf __pycache__


# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

# run uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--reload"]
