# app.py

import logging
from flask import Flask, request, jsonify, render_template, Response
import json
from langchain_google_genai import ChatGoogleGenerativeAI # untuk classifier
from rag_core import get_conversational_rag_chain

logging.basicConfig(filename='feedback.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s')

app = Flask(__name__)
sessions = {}


# Inisialisasi LLM khusus untuk tugas klasifikasi
classifier_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0)

# Jawaban yang sudah disiapkan untuk kategori non-kebijakan
CANNED_RESPONSES = {
    "SAPAAN": "Halo! Ada yang bisa saya bantu terkait kebijakan kepegawaian BKI?",
    "TENTANG_BOT": "Saya adalah SMART HC, asisten AI yang dirancang untuk menjawab pertanyaan seputar kebijakan kepegawaian BKI berdasarkan dokumen yang ada. Saya tidak memiliki opini atau kesadaran pribadi.",
    "TIDAK_RELEVAN": "Maaf, saya hanya bisa menjawab pertanyaan yang berhubungan dengan kebijakan kepegawaian BKI. Ada lagi yang bisa saya bantu?"
}


def classify_question(question: str) -> str:
    """
    Menggunakan LLM untuk mengklasifikasikan pertanyaan pengguna.
    """
    prompt = f"""
    Klasifikasikan pertanyaan pengguna ke dalam salah satu kategori berikut: SAPAAN, TENTANG_BOT, KEBIJAKAN_PERUSAHAAN.

    - SAPAAN: Jika pengguna hanya menyapa. Contoh: halo, selamat pagi, hi.
    - TENTANG_BOT: Jika pengguna bertanya tentang identitas atau kemampuan bot. Contoh: kamu siapa? apakah kamu pintar? kamu bisa apa saja?
    - KEBIJAKAN_PERUSAHAAN: Jika pengguna bertanya tentang peraturan, hak, atau kewajiban sebagai pegawai. Contoh: bagaimana cara klaim kacamata? berapa hari cuti tahunan?

    Pertanyaan: "{question}"
    Kategori:
    """
    try:
        response = classifier_llm.invoke(prompt)
        category = response.content.strip().upper()
        if category in CANNED_RESPONSES:
            return category
        return "KEBIJAKAN_PERUSAHAAN"  # Default jika tidak cocok
    except Exception:
        return "KEBIJAKAN_PERUSAHAAN"  # Jika terjadi error, anggap sebagai pertanyaan kebijakan


def stream_canned_response(category: str):
    """
    Melakukan streaming untuk jawaban yang sudah disiapkan.
    """
    response_text = CANNED_RESPONSES.get(category, CANNED_RESPONSES["TIDAK_RELEVAN"])
    for word in response_text.split():
        yield f"data: {json.dumps({'type': 'token', 'content': word + ' '})}\n\n"
    # Kirim sumber kosong karena ini bukan dari dokumen
    yield f"data: {json.dumps({'type': 'sources', 'content': []})}\n\n"



@app.route("/")
def index():
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question")
    session_id = data.get("session_id")

    if not all([question, session_id]):
        return jsonify({"error": "Question and session_id are required"}), 400

    # --- LOGIKA ROUTER BARU ---

    # 1. Klasifikasikan pertanyaan terlebih dahulu
    category = classify_question(question)

    # 2. Jika bukan pertanyaan kebijakan, berikan jawaban siap pakai
    if category != "KEBIJAKAN_PERUSAHAAN":
        return Response(stream_canned_response(category), mimetype='text/event-stream')

    # 3. Jika pertanyaan kebijakan, lanjutkan dengan alur RAG
    if session_id not in sessions:
        sessions[session_id] = get_conversational_rag_chain()

    chain = sessions[session_id]

    def stream_response():
        final_answer = ""
        # Kita tidak perlu lagi variabel source_documents
        for chunk in chain.stream({"question": question}):
            # Sekarang output chain hanya 'answer'
            word = chunk.get("answer", "")
            final_answer += word
            yield f"data: {json.dumps({'type': 'token', 'content': word})}\n\n"

    return Response(stream_response(), mimetype='text/event-stream')

@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json()
    question = data.get("question")
    answer = data.get("answer")
    feedback_type = data.get("feedback_type")
    logging.info(f"FEEDBACK: {feedback_type.upper()} | Q: {question} | A: {answer}")
    return jsonify({"status": "success", "message": "Feedback received"}), 200


if __name__ == "__main__":
    # Disarankan tetap menggunakan waitress untuk streaming yang lebih baik
    # waitress-serve --host=127.0.0.1 --port=5001 app:app
    app.run(debug=True, port=5001)