# ingest_data.py
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

# Lokasi penyimpanan database vektor dan folder dokumen
CHROMA_PATH = "vector_store"
DATA_PATH = "documents"


def main():
    # 1. Muat dokumen dari folder
    loader = DirectoryLoader(DATA_PATH, glob="*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()

    # 2. Bagi teks menjadi potongan-potongan kecil (chunks)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)
    print(f"Total chunks: {len(chunks)}")

    # 3. Buat embedding dan simpan ke ChromaDB
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

    db = Chroma.from_documents(
        chunks, embeddings, persist_directory=CHROMA_PATH
    )
    db.persist()
    print(f"Data berhasil disimpan di {CHROMA_PATH}")


if __name__ == "__main__":
    main()