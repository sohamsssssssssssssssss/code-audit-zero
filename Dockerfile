FROM ubuntu:latest
LABEL authors="atharva"

ENTRYPOINT ["top", "-b"]