import os
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from config.config import get_config


class Qdrant:
    def __init__(self, host=None, port=None, collection_name=None):
        host = host or os.environ.get("QDRANT_HOST", "localhost")
        port = port or int(os.environ.get("QDRANT_PORT", 6333))
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name or get_config("COLLECTION")
        embedding_model = get_config("EMBEDDING_MODEL")
        self.dimension = get_config("EMBEDDING_DIMENSION")[embedding_model]

    def create_collection(self, reset=False):
        existe = self.client.collection_exists(self.collection_name)
        if existe and reset:
            self.client.delete_collection(self.collection_name)
            existe = False
        if not existe:
            self.client.create_collection(
                self.collection_name,
                vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE),
            )

    def upsert_chunks(self, textes, vecteurs, metadatas):
        """
        Un point par chunk. L'id est déterministe (uuid5 dérivé de arxiv_id + version +
        section + chunk_index) : ré-indexer le même papier met à jour ses points au lieu
        de les dupliquer.
        """
        points = [
            PointStruct(
                id=str(uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"{meta['arxiv_id']}v{meta['version']}/{meta.get('section', '')}/{meta['chunk_index']}",
                )),
                vector=vecteur,
                payload={**meta, "texte": texte},
            )
            for texte, vecteur, meta in zip(textes, vecteurs, metadatas)
        ]
        self.client.upsert(collection_name=self.collection_name, points=points)

    def search(self, query_vector, top_k=5, query_filter=None):
        return self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        )
