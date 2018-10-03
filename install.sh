#!/usr/bin/env bash
set -e

echo "Have you sourced the env script first?"

pip3 install setuptools
pip3 install awscli==1.11.18
pip3 install boto3
pip3 install pyserial

echo "configure aws"