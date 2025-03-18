import chromadb
chroma_client = chromadb.PersistentClient(path="./chroma_db")

COLLECTION_NAME = "images"
chroma = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
