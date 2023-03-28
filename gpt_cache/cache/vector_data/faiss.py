import os

import faiss
from faiss import IndexHNSWFlat, Index
import numpy as np


class Faiss:
    index: Index

    def __init__(self, index_file_path, dimension, top_k=1, skip_file=False):
        self.index_file_path = index_file_path
        self.index = IndexHNSWFlat(dimension, 32)
        self.top_k = top_k
        if os.path.isfile(index_file_path) and not skip_file:
            self.index = faiss.read_index(index_file_path)

    def add(self, data):
        np_data = np.array(data).astype('float32').reshape(1, -1)
        self.index.add(np_data)

    def mult_add(self, datas):
        np_data = np.array(datas).astype('float32')
        self.index.add(np_data)

    def search(self, data):
        np_data = np.array(data).astype('float32').reshape(1, -1)
        D, I = self.index.search(np_data, self.top_k)
        distances = []
        for d in D[:1].reshape(-1):
            if d >= 655:
                distances.append(int(65500))
            else:
                distances.append(int(d) * 100)
        vector_datas = [self.index.reconstruct(int(i)) for i in I[:1].reshape(-1)]
        return zip(distances, vector_datas)

    def close(self):
        faiss.write_index(self.index, self.index_file_path)