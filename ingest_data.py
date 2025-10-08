# ingest_data.py (Versi Final dengan Link Markdown)

import os
import shutil
from dotenv import load_dotenv
from urllib.parse import quote  # Import baru untuk URL encoding
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

CHROMA_PATH = "vector_store"
DATA_PATH = "documents"
# --- VARIABEL BARU: Tentukan Base URL untuk file PDF Anda ---
# Untuk pengembangan lokal dengan folder static/pdf
BASE_PDF_URL = "http://127.0.0.1:5001/static/kebijakan/"


def main():
    loader = DirectoryLoader(DATA_PATH, glob="*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)

    # Tanam LINK MARKDOWN LENGKAP ke dalam konten setiap chunk
    for chunk in chunks:
        file_name = os.path.basename(chunk.metadata.get("source", "N/A"))
        page_number = chunk.metadata.get("page", -1) + 1

        # Buat URL yang aman
        safe_file_name = quote(file_name)
        full_url = f"{BASE_PDF_URL}{safe_file_name}#page={page_number}"
        markdown_link = f"**[Sumber: {file_name}, Hal. {page_number}]({full_url})**"
        chunk.page_content = f"{markdown_link}\n\n{chunk.page_content}"

        # Buat link Markdown lengkap
        markdown_link = f"**[Sumber: {file_name}, Hal. {page_number}]({full_url})**"

        # Gabungkan link dengan konten asli
        chunk.page_content = f"{markdown_link}\n\n{chunk.page_content}"

    print(f"Total chunks yang akan diproses: {len(chunks)}")

    if os.path.exists(CHROMA_PATH):
        print(f"Menghapus database lama di {CHROMA_PATH}...")
        shutil.rmtree(CHROMA_PATH)

    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

    db = Chroma.from_documents(
        chunks, embeddings, persist_directory=CHROMA_PATH
    )
    db.persist()
    print(f"Data baru berhasil dibuat dan disimpan di {CHROMA_PATH}")


if __name__ == "__main__":
    main()