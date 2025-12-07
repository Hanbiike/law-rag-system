from sentence_transformers import SentenceTransformer
import os
import torch
import numpy as np

os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Check if CUDA is available
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Using device: {device}")
if device == 'cuda':
    print(f"GPU: {torch.cuda.get_device_name(0)}")

# Download from the 🤗 Hub and load to CUDA if available
model = SentenceTransformer("google/embeddinggemma-300m", device=device)

def encode_queries(queries) -> list:
    """Encode queries using the SentenceTransformer model"""
    tensors = model.encode(queries, convert_to_tensor=True, device=device)
    return [tensor.cpu().numpy() for tensor in tensors]

def similarity(a, b):
    """Compute cosine similarity between two vectors"""
    return model.similarity(a, b)
