#!/bin/bash
#Only required to build the Lambda layer libraries
docker build -t ce-report-build .
docker run --rm -v ${PWD}/bin:/vol ce-report-build
