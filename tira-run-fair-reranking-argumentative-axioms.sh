#!/usr/bin/env bash

./tira-run.sh "$1" "$2" "grimjack-fair-reranking-argumentative-axioms" \
  --retrieval-model query-likelihood-dirichlet \
  --targer-model tag-ibm-fasttext \
  --quality-tagger debater \
  --stance-tagger debater-sentiment \
  --stance-threshold 0.125 \
  --num-hits 100 \
  --rerank-hits 10 \
  --reranker axiomatic \
  --argumentative-axioms \
  --reranker subjective-first \
  --reranker alternating-stance
