#!/usr/bin/env bash

set -e

cp ~/atlas-pi/.bashrc ~/
source ~/.bashrc

pip install setuptools
pip install awscli
pip install boto3
pip install pyserial