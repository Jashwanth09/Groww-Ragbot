import sys, numpy as np
sys.path.append('phase2')
from vector_store_manager import VectorStoreManager
m = VectorStoreManager()
m.load_existing_index()
q = np.random.rand(1, 384).astype(np.float32)
res = m.search(q, 10)
print("Search results:", len(res))
