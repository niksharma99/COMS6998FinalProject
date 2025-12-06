#!/bin/bash

# Google Drive FILE IDs
MOVIE_ID="1ld84nIDTzt_1DGxngMBn7n8Yp6mHP4tk" 
USER_ID="1qOhnyLKPCYxeueeMgxy__GS9SatdTg6I"  

OUT_DIR="./TasteEmbeddingGenerator/artifacts"
mkdir -p $OUT_DIR

echo "Downloading movie_embeddings.parquet..."
curl -L "https://drive.google.com/uc?export=download&id=${MOVIE_ID}" -o "${OUT_DIR}/movie_embeddings.parquet"

echo "Downloading user_embeddings.parquet..."
curl -L "https://drive.google.com/uc?export=download&id=${USER_ID}" -o "${OUT_DIR}/user_embeddings.parquet"

echo "Done! Files saved in ${OUT_DIR}/"
