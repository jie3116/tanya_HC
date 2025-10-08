# app.py

import logging
import os
from flask import Flask, request, jsonify, render_template, Response, session
from flask_session import Session
import json
from langchain_google_genai import ChatGoogleGenerativeAI # untuk classifier
from rag_core import get_conversational_rag_chain

logging.basicConfig(filename='feedback.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s')

app = Flask(__name__)

# 1. Atur Secret Key dari environment variable
app.secret_key = os.environ.get("SECRET_KEY", "70177c807b9bc314da08ade38e2c6ee4692edee24b7d94df")

# 2. Konfigurasi Flask-Session untuk menyimpan file di sistem file
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_USE_SIGNER"] = True
# path di dalam container yang akan di-mount sebagai volume
app.config["SESSION_FILE_DIR"] = os.environ.get("SESSION_FILE_DIR", "./flask_session")

# 3. Inisialisasi ekstensi Session
server_session = Session(app)


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
    response_text = CANNED_RESPONSES.get(category, CANNED_RESPONSES["TIDAK_RELEVAN"])
    full_response = " ".join(response_text.split()) # Gabungkan kembali
    yield f"data: {json.dumps({'type': 'token', 'content': full_response})}\n\n"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question")

    if not question:
        return jsonify({"error": "Question is required"}), 400

    category = classify_question(question)

    if category != "KEBIJAKAN_PERUSAHAAN":
        return Response(stream_canned_response(category), mimetype='text/event-stream')

    # Periksa apakah RAG chain sudah ada di dalam 'session'
    if 'rag_chain' not in session:
        print("Membuat RAG chain baru untuk sesi ini...")
        # Jika belum, buat dan simpan di session
        session['rag_chain'] = get_conversational_rag_chain()

    # Ambil chain dari session
    chain = session['rag_chain']

    def stream_response():
        final_answer = ""
        for chunk in chain.stream({"question": question}):
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
    app.run(debug=True, port=5001)