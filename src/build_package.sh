#!/bin/bash
#script designed to work as part of Docker build process (build_bin.sh)
rm /vol/lambda.zip
zip -r /vol/lambda.zip lambda.py ./vendored