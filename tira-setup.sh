#!/usr/bin/env bash

if [[ $UID != 0 ]]; then
  echo "Please run this script with sudo:"
  echo "sudo $0 $*"
  exit 1
fi

# Install System dependencies.
apt-get -y update
apt-get -y install git openjdk-11-jdk python3.9 python3.9-venv python3-pip

# Install Python dependencies.
python3.9 -m ensurepip --upgrade
pip3 install --upgrade pip
pip3 install pipenv