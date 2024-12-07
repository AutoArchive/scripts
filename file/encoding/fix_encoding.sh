#!/bin/bash

# Exit on any error
set -e

python .github/scripts/file/encoding/encoding_simple.py
python .github/scripts/file/encoding/encoding.py

echo "Encoding fixed successfully!"
