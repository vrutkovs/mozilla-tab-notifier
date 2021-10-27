FROM registry.access.redhat.com/ubi8/ubi:8.4
RUN dnf install -y python3 lz4 lz4-devel \
    && dnf clean all
RUN pip3 install paho-mqtt lz4
WORKDIR /code
COPY . .
CMD ["python3", "main.py"]
