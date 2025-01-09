#!/bin/bash

# Exit on any error
set -e
sudo apt update
sudo apt install antiword
pip install -r .github/scripts/requirements.txt
