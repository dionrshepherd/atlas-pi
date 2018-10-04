#!/usr/bin/env bash
set -e

echo "Have you sourced the env script first?"

apt install python3-pip
pip3 install setuptools
pip3 install awscli==1.11.18
pip3 install boto3
pip3 install pyserial

echo "run: ./.local/bin/aws configure"