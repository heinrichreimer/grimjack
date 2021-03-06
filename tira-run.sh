#!/usr/bin/env bash

# Configure task inputs.
topic_file_name="topics.xml"
documents_file_name="passages.jsonl.gz"
run_file_name="run.txt"

# Parse script options (paths and tag).
if [ $# -lt 3 ]; then
  echo "Usage: $0 input_dir output_dir run_tag [options...]"
  exit 1
fi
input_dir=$1
output_dir=$2
run_tag=$3
shift 3

# Determine input and output file paths.
input_topic_file="$input_dir/$topic_file_name"
input_documents_file="$input_dir/$documents_file_name"
output_run_file="$output_dir/$run_file_name"

# Create output folder if not exists.
mkdir -p "$output_dir"

# List input and output files.
echo "$input_topic_file"
echo "$input_documents_file"
echo "$output_run_file"

# Generate internal run file.
/home/grimjack/.local/bin/pipenv run python -m grimjack \
  --topics-path "$input_topic_file" \
  --documents-path "$input_documents_file" \
  "$@" \
  --verbose \
  run \
  --tag "$run_tag" \
  "$output_run_file"
