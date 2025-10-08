# check_db.py (Versi yang Diperbaiki)

from dotenv import load_dotenv  # <-- BARIS BARU 1: Import library dotenv
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Muat variabel dari file .env (termasuk GOOGLE_API_KEY)
load_dotenv()  # <-- BARIS BARU 2: Panggil fungsi untuk memuat .env

# Pastikan CHROMA_PATH sesuai dengan yang ada di proyek Anda
CHROMA_PATH = "vector_store"


def check_database_content():
    print("Mencoba memuat database vektor...")

    # Sekarang baris ini akan berhasil karena API Key sudah dimuat
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)

    print("Database berhasil dimuat. Mengambil satu dokumen acak...")

    retrieved_docs = db.similarity_search("cuti", k=1)

    if not retrieved_docs:
        print("\n!!! PERINGATAN: Tidak ada dokumen yang ditemukan di database. Coba jalankan ulang ingest_data.py !!!")
        return

    first_doc = retrieved_docs[0]

    print("\n--- ISI DOKUMEN PERTAMA YANG DITEMUKAN ---")
    print(first_doc.page_content)
    print("------------------------------------------")

    if "http" in first_doc.page_content and "](" in first_doc.page_content:
        print(
            "\n✅ KESIMPULAN: Link Markdown DITEMUKAN di dalam database. Masalah kemungkinan ada di backend (LLM) atau frontend.")
    else:
        print(
            "\n❌ KESIMPULAN: Link Markdown TIDAK DITEMUKAN. Masalah ada di `ingest_data.py` atau Anda belum menjalankan ulangnya. Pastikan `ingest_data.py` Anda sudah benar dan jalankan lagi.")


if __name__ == "__main__":
    check_database_content()