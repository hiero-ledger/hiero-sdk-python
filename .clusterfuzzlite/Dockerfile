FROM gcr.io/oss-fuzz-base/base-builder-python

COPY . $SRC/hiero-sdk-python
WORKDIR $SRC/hiero-sdk-python
COPY .clusterfuzzlite/build.sh $SRC/build.sh
