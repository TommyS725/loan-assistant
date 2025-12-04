from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)
from langchain_chroma import Chroma
import os
from langchain_core.documents import Document
from langchain_ibm import WatsonxEmbeddings
from watsonx import credentials, WATSONX_PROJECT_ID
from ibm_watsonx_ai.metanames import EmbedTextParamsMetaNames as EmbedParams
from typing import List, Optional
import glob
import shutil


embed_params = {
    EmbedParams.RETURN_OPTIONS: {"input_text": True},
}


class RAG:

    def __init__(
        self,
        documents_dir: str = "documents/",
        persist_directory: str = "./chroma_db",
        force_recreate: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.documents_dir = documents_dir
        self.persist_directory = persist_directory
        self.vector_store = None
        self.embeddings = None
        self._initialize_rag_system(force_recreate)

    def _initialize_rag_system(self, force_recreate: bool = False):
        """Initialize the RAG system with persistence"""
        # Initialize embeddings
        self.embeddings = WatsonxEmbeddings(
            model_id="ibm/slate-30m-english-rtrvr-v2",
            url=credentials.get("url"),
            project_id=WATSONX_PROJECT_ID,
            params=embed_params,
        )
        print("Embeddings initialized successfully.")

        # Check if vector store already exists and we don't want to force recreate
        if not force_recreate and os.path.exists(self.persist_directory):
            try:
                # Load existing vector store
                self.vector_store = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings,
                )

                # Check if collection has documents
                collection_count = self.vector_store._collection.count()
                print(
                    f"Loaded existing vector store with {collection_count} documents."
                )
                return
            except Exception as e:
                print(f"Error loading existing vector store: {e}")
                print("Creating new vector store...")

        # Create new vector store
        self._create_new_vector_store()

    def _create_new_vector_store(self):
        # delete existing directory if it exists
        if os.path.exists(self.persist_directory):
            shutil.rmtree(self.persist_directory)
            print(f"Deleted existing vector store directory: {self.persist_directory}")
        """Create a new vector store from documents"""
        # Load all text files from documents directory
        documents = self._load_documents()
        print(f"Loaded {len(documents)} documents.")

        if not documents:
            print("Warning: No documents found in", self.documents_dir)
            # Create empty vector store
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
            )
            return

        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )

        splits = text_splitter.split_documents(documents)
        print(f"Split into {len(splits)} document chunks.")

        # Create and persist vector store
        self.vector_store = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory=self.persist_directory,
        )
        print(f"Created new vector store and persisted to {self.persist_directory}")

    def _load_documents(self) -> List[Document]:
        """Load all text files from the documents directory"""
        documents = []

        # Check if documents directory exists
        if not os.path.exists(self.documents_dir):
            print(f"Creating documents directory: {self.documents_dir}")
            os.makedirs(self.documents_dir, exist_ok=True)
            return documents

        # Find all text files
        txt_files = glob.glob(os.path.join(self.documents_dir, "*.txt"))

        for file_path in txt_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Extract filename without extension as metadata
                filename = os.path.basename(file_path)
                title = os.path.splitext(filename)[0].replace("_", " ").title()

                # Create Document object
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": filename,
                        "title": title,
                        "type": "loan_document",
                    },
                )
                documents.append(doc)

            except Exception as e:
                print(f"Error loading {file_path}: {e}")

        return documents

    def search(self, query: str, k: int = 5):
        """Search the vector store for similar documents"""
        if not self.vector_store:
            print("Vector store is not initialized.")
            return []

        results = self.vector_store.similarity_search(query, k=k)
        return results

    async def asearch(self, query: str, k: int = 5):
        """Asynchronous search the vector store for similar documents"""
        if not self.vector_store:
            print("Vector store is not initialized.")
            return []

        results = await self.vector_store.asimilarity_search(query, k=k)
        return results

    def add_document(self, file_path: str):
        """Add a single document to the vector store"""
        if not self.vector_store:
            print("Vector store is not initialized.")
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract filename without extension as metadata
            filename = os.path.basename(file_path)
            title = os.path.splitext(filename)[0].replace("_", " ").title()

            # Create Document object
            doc = Document(
                page_content=content,
                metadata={
                    "source": filename,
                    "title": title,
                    "type": "loan_document",
                },
            )

            # Split the document
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                separators=["\n\n", "\n", " ", ""],
            )

            splits = text_splitter.split_documents([doc])

            # Add to vector store
            self.vector_store.add_documents(splits)
            print(f"Added document: {filename} ({len(splits)} chunks)")

        except Exception as e:
            print(f"Error adding document {file_path}: {e}")

    def delete_collection(self):
        """Delete the entire vector store collection"""
        if self.vector_store:
            self.vector_store.delete_collection()
            print("Vector store collection deleted.")

    def get_collection_info(self):
        """Get information about the vector store collection"""
        if not self.vector_store:
            return {"error": "Vector store not initialized"}

        try:
            count = self.vector_store._collection.count()
            return {
                "document_count": count,
                "persist_directory": self.persist_directory,
                "collection_name": self.vector_store._collection.name,
            }
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    # Example usage

    # Option 1: Load existing vector store (default)
    print("=== Loading existing vector store ===")
    rag_system = RAG(
        documents_dir="documents/",
        persist_directory="./chroma_db",
        force_recreate=False,
    )
    print("RAG system initialized.")

    # Get collection info
    info = rag_system.get_collection_info()
    print(f"Collection info: {info}")

    # Search
    query = "meaning of personal loan mortgage loan auto loan small business loan student loan emergency medical loan home improvement loan debt consolidation loan"
    results = rag_system.search(query, k=5)

    print("Search Results:")
    for idx, doc in enumerate(results):
        print(f"Result {idx + 1}:")
        print(f"Title: {doc.metadata.get('title', 'N/A')}")
        print(f"Source: {doc.metadata.get('source', 'N/A')}")
        print(f"Content Snippet: {doc.page_content[:200]}...")
        print("-" * 40)
