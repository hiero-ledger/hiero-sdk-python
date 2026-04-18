FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:c1629d34bc645be7551e1ade467aff32ec2058875f2b27eb5471d964374d3d1e

COPY . $SRC/hiero-sdk-python
WORKDIR $SRC/hiero-sdk-python
COPY .clusterfuzzlite/build.sh $SRC/build.sh
