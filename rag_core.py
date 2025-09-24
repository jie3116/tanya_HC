# rag_core.py

from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

load_dotenv()

CHROMA_PATH = "vector_store"

# Template prompt yang diperbarui untuk meminta output Markdown
PROMPT_TEMPLATE = """Gunakan informasi berikut untuk menjawab pertanyaan pengguna. Jawaban harus berdasarkan konteks yang diberikan.
Jika Anda tidak tahu jawabannya, katakan saja Anda tidak tahu, jangan mencoba mengarang jawaban.
Selalu format jawabanmu menggunakan Markdown (misalnya untuk daftar, gunakan - atau 1., 2., dst).

Konteks: {context}
Riwayat Obrolan: {chat_history}
Pertanyaan: {question}
Jawaban:
"""


def get_conversational_rag_chain():
    """
    Menyiapkan dan mengembalikan RAG chain dengan memori percakapan.
    """
    # Siapkan embedding model dan koneksi ke ChromaDB
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)

    # Buat retriever untuk mencari dokumen relevan
    retriever = db.as_retriever(search_kwargs={'k': 3})  # Ambil 3 dokumen paling relevan

    # Buat memori untuk menyimpan riwayat percakapan
    # return_messages=True agar bisa diproses oleh chain
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key='answer'  # Tentukan kunci output agar sumber bisa diambil
    )

    # Inisialisasi model Gemini (gunakan Flash untuk kecepatan dan kuota)
    model = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash-latest",
        temperature=0.3,
        streaming=True  # Aktifkan streaming
    )

    # Buat RAG chain yang mendukung percakapan
    chain = ConversationalRetrievalChain.from_llm(
        llm=model,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,  # Kembalikan dokumen sumber
        combine_docs_chain_kwargs={
            "prompt": PromptTemplate.from_template(PROMPT_TEMPLATE)
        }
    )

    return chain