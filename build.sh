#!/bin/bash
docker build -t ce-report-build .
docker run --rm -v ${PWD}/bin:/vol ce-report-build
