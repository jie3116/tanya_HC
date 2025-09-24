# app.py (Ganti seluruh isi file dengan ini)

import logging
from flask import Flask, request, jsonify, render_template, Response
from sse_starlette.sse import EventSourceResponse
import json

from rag_core import get_conversational_rag_chain

# Konfigurasi logging untuk umpan balik
logging.basicConfig(filename='feedback.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s')

app = Flask(__name__)

# "Sesi" sederhana menggunakan dictionary di memori
# Dalam produksi, gunakan solusi yang lebih baik seperti Flask-Session atau Redis
sessions = {}


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

    # Dapatkan atau buat chain untuk sesi ini
    if session_id not in sessions:
        sessions[session_id] = get_conversational_rag_chain()

    chain = sessions[session_id]

    def stream_response():
        final_answer = ""
        source_documents = []

        # Menggunakan stream untuk mendapatkan respons kata per kata
        for chunk in chain.stream({"question": question}):
            if "answer" in chunk:
                word = chunk["answer"]
                final_answer += word
                # Kirim setiap kata sebagai Server-Sent Event (SSE)
                yield f"data: {json.dumps({'type': 'token', 'content': word})}\n\n"

            if "source_documents" in chunk:
                source_documents = chunk["source_documents"]

        # Setelah streaming selesai, kirim dokumen sumber
        sources = [
            {"source": doc.metadata.get("source", "N/A"), "page": doc.metadata.get("page", "N/A")}
            for doc in source_documents
        ]
        yield f"data: {json.dumps({'type': 'sources', 'content': sources})}\n\n"

    # Menggunakan Response object dari Flask untuk streaming
    return Response(stream_response(), mimetype='text/event-stream')


@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json()
    question = data.get("question")
    answer = data.get("answer")
    feedback_type = data.get("feedback_type")  # "like" or "dislike"

    # Log umpan balik ke file
    logging.info(f"FEEDBACK: {feedback_type.upper()} | Q: {question} | A: {answer}")

    return jsonify({"status": "success", "message": "Feedback received"}), 200


if __name__ == "__main__":
    app.run(debug=True, port=5001)