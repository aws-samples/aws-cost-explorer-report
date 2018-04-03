#!/bin/bash
#script designed to work as part of Docker build process (build_bin.sh)
rm /vol/lambda.zip
zip -ur /vol/lambda.zip lambda.py
cd requirements
zip -ur /vol/lambda.zip ./
