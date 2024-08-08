FROM debian:buster-slim

WORKDIR /work

# Install dependencies
RUN apt update
RUN apt install tor python3 python3-pip curl -y
COPY requirements.txt .
RUN pip3 install -r requirements.txt

ENV PYTHONUNBUFFERED=1

# Copy working files
COPY docker-init.sh .
COPY code/ .

CMD ["sh", "/work/docker-init.sh"]