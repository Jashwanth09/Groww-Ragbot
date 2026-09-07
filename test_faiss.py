import sys, numpy as np
sys.path.append('phase2')
import traceback

try:
    from vector_store_manager import VectorStoreManager
    m = VectorStoreManager()
    m.load_existing_index()
    q = np.random.rand(1, m.index.d).astype(np.float32)
    distances, indices = m.index.search(q, 10)
    print("Search executed successfully!")
    print("distances shape:", distances.shape)
    print("ntotal:", m.index.ntotal)
except Exception as e:
    import traceback
    traceback.print_exc()
    traceback.print_exc()
