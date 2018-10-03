#!/usr/bin/env bash

set -e

cp ~/atlas-pi/.bashrc ~/

pip install awscli
pip install boto3
pip install pyserial