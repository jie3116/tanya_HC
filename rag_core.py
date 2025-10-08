# rag_core.py

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

load_dotenv()

CHROMA_PATH = "vector_store"

# Prompt sekarang lebih sederhana, karena sumber sudah ada di dalam {context}
PROMPT_TEMPLATE = """Anda adalah SMART HC, asisten AI yang berpengetahuan tentang kebijakan kepegawaian BKI.
Jawab pertanyaan pengguna dengan ramah, jelas, dan langsung ke intinya. Gunakan hanya informasi dari 'Konteks' di bawah ini.
Setiap bagian dari konteks sudah diawali dengan informasinya sumbernya, seperti [Sumber: nama_file.pdf, Hal. X].

Instruksi Jawaban:
1.  Berikan jawaban yang jelas dalam format Markdown.
2.  Setelah memberikan jawaban utama, periksa konteks yang Anda gunakan. Jika Anda menemukan referensi ke nomor "Pasal" atau "Bab" yang relevan dengan jawaban, buatlah bagian baru berjudul "**Pasal Terkait:**" dan sebutkan nomor pasal/bab tersebut.
3.  Di bagian paling akhir, buatlah bagian berjudul "**Sumber:**" dan sebutkan kembali tag sumber lengkap dengan link-nya, persis seperti yang ada di konteks.
4.  Jika informasi tidak ada di konteks, katakan Anda tidak tahu. Jangan mengarang.
5.  Jangan pernah memulai jawaban dengan "Berdasarkan konteks...".


Konteks:
{context}

Riwayat Obrolan:
{chat_history}

Pertanyaan: {question}
Jawaban:
"""


def get_conversational_rag_chain():
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
    retriever = db.as_retriever(search_kwargs={'k': 3})

    memory = ConversationBufferMemory(
        memory_key="chat_history", return_messages=True, output_key='answer'
    )

    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", temperature=0.1, streaming=True
    )

    # Pembuatan chain kembali sederhana
    chain = ConversationalRetrievalChain.from_llm(
        llm=model,
        retriever=retriever,
        memory=memory,
        return_source_documents=False,  # Tetap False
        combine_docs_chain_kwargs={
            "prompt": PromptTemplate.from_template(PROMPT_TEMPLATE)
        }
    )

    return chain