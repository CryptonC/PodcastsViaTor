FROM debian:buster-slim

WORKDIR /work

# Install dependencies
RUN apt update
RUN apt install tor torsocks python3 curl -y

ENV PYTHONUNBUFFERED=1

# Copy working files
COPY docker-init.sh .
COPY code/ .

CMD ["sh", "/work/docker-init.sh"]