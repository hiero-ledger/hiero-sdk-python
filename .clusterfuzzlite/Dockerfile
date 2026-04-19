FROM gcr.io/oss-fuzz-base/base-builder-python

RUN apt-get update && apt-get install -y --no-install-recommends \
    protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

COPY . $SRC/hiero-sdk-python
WORKDIR $SRC/hiero-sdk-python
COPY .clusterfuzzlite/build.sh $SRC/
