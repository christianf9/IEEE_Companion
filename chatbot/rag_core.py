import faiss
import pickle
from pymongo import MongoClient
import math

class KnowledgeFlow:
    def __init__(self, db, db_name, index_collection_name, texts_collection_name, dimension):
        self.client = db
        self.db = self.client[db_name]
        self.index_collection = self.db[index_collection_name]
        self.texts_collection = self.db[texts_collection_name]
        self.dimension = dimension
        self.index = None
        self.last_retrain_size = 0

    def create_or_update_vector_store(self, session_id, vectors, texts):
        # Load existing vector store if it exists
        data = self.index_collection.find_one({"session_id": session_id})
        if data:
            self.index = pickle.loads(data["index"])
            self.last_retrain_size = data.get("last_retrain_size", 0)
        else:
            # Initialize with Flat index for fewer than 10,000 vectors
            self.index = faiss.IndexFlatL2(self.dimension)
            self.last_retrain_size = 0

        # Add vectors to the index
        current_data_point_count = self._get_data_point_count(session_id)
        if current_data_point_count + len(vectors) >= 10000:  # Switch to IVF after 10,000 vectors
            if not isinstance(self.index, faiss.IndexIVFFlat):
                self._initialize_ivf_index(vectors)
            self._update_ivf_index(vectors, session_id)
        else:
            self.index.add(vectors)

        # Save texts to the separate collection
        self._save_texts(session_id, vectors, texts)

        # Save updated vector store to MongoDB
        self._save_vector_store(session_id)

    def search_vector_store(self, session_id, query_vector, k):
        # Load vector store for the session
        self._load_vector_store(session_id)

        if not self.index:
            raise ValueError(f"No vector store found for session ID: {session_id}")

        if isinstance(self.index, faiss.IndexIVFFlat):
            self.index.nprobe = math.ceil(math.sqrt(self.index.nlist))  # Adjust nprobe dynamically

        # Perform the search
        distances, indices = self.index.search(query_vector.reshape(1, -1), k)
        results = self._get_texts_by_vector_ids(session_id, indices[0])
        return results

    def _initialize_ivf_index(self, vectors):
        num_clusters = math.ceil(math.sqrt(self._get_data_point_count(None) + len(vectors)))
        quantizer = faiss.IndexFlatL2(self.dimension)
        self.index = faiss.IndexIVFFlat(quantizer, self.dimension, num_clusters)
        self.index.train(vectors)  # Train with the new data
        self.last_retrain_size = self._get_data_point_count(None) + len(vectors)

    def _update_ivf_index(self, vectors, session_id):
        total_vectors = self._get_data_point_count(session_id) + len(vectors)
        growth_factor = total_vectors / max(1, self.last_retrain_size)

        if growth_factor > 1.2:  # Retrain if size grows by more than 20%
            num_clusters = math.ceil(math.sqrt(total_vectors))
            quantizer = faiss.IndexFlatL2(self.dimension)
            self.index = faiss.IndexIVFFlat(quantizer, self.dimension, num_clusters)
            self.index.train(vectors)
            self.last_retrain_size = total_vectors

        self.index.add(vectors)

    def _save_vector_store(self, session_id):
        serialized_index = pickle.dumps(self.index)
        self.index_collection.replace_one(
            {"session_id": session_id},
            {
                "session_id": session_id,
                "index": serialized_index,
                "last_retrain_size": self.last_retrain_size,
            },
            upsert=True,
        )

    def _load_vector_store(self, session_id):
        data = self.index_collection.find_one({"session_id": session_id})
        if data:
            self.index = pickle.loads(data["index"])
            self.last_retrain_size = data.get("last_retrain_size", 0)
        else:
            raise ValueError(f"No vector store found for session ID: {session_id}")

    def _save_texts(self, session_id, vectors, texts):
        current_count = self._get_data_point_count(session_id)
        vector_ids = range(current_count, current_count + len(vectors))
        documents = [{"session_id": session_id, "vector_id": vid, "text": text} for vid, text in zip(vector_ids, texts)]
        self.texts_collection.insert_many(documents)

    def _get_texts_by_vector_ids(self, session_id, vector_ids):
        # Ensure all vector_ids are Python integers
        vector_ids = [int(v) for v in vector_ids if v != -1]
        results = self.texts_collection.find({"session_id": session_id, "vector_id": {"$in": vector_ids}})
        vector_id_to_text = {doc["vector_id"]: doc["text"] for doc in results}
        # Return texts in the order of vector_ids
        return [vector_id_to_text.get(v_id, "") for v_id in vector_ids]

    def _get_data_point_count(self, session_id):
        if session_id:
            return self.texts_collection.count_documents({"session_id": session_id})
        else:
            return self.texts_collection.count_documents({})