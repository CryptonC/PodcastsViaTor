FROM debian:buster-slim

WORKDIR /work

# Install dependencies
RUN apt update
RUN apt install tor python3 python3-pip firefox-esr -y
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Install geckodriver based on target architecture
ARG TARGETARCH
RUN apt install curl -y
RUN if [ "$TARGETARCH" = "arm64" ]; then echo "geckodriver-v0.35.0-linux-aarch64.tar.gz" > targetFile; else echo "geckodriver-v0.35.0-linux64.tar.gz" > targetFile; fi
RUN curl -L https://github.com/mozilla/geckodriver/releases/download/v0.35.0/$(cat targetFile) -o geckodriver.tar.gz
RUN rm targetFile
RUN tar -xzf geckodriver.tar.gz
RUN chmod +x geckodriver
RUN mv geckodriver /usr/local/bin/

ENV PYTHONUNBUFFERED=1

# Copy working files
COPY docker-init.sh .
COPY code/ .

CMD ["sh", "/work/docker-init.sh"]