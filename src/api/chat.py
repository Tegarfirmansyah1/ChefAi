import os
import json
import traceback
from http.server import BaseHTTPRequestHandler
# --- Import Pustaka LangChain ---
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_core.runnables import RunnableBranch, RunnableLambda
from pathlib import Path

# --- Fungsi Helper ---
def extract_intent(llm_output):
    return llm_output.content.strip()

def get_greeting_response(_):
    return {"answer": "Halo! Saya Chef Chimi, asisten resep virtual Anda. Ada yang bisa saya bantu?"}

def get_self_intro_response(_):
    return {"answer": "Saya Chef Chimi! Saya siap membantu Anda menemukan resep masakan Indonesia dari database saya."}

def get_rejection_response(_):
    return {"answer": "Maaf, sebagai Chef Chimi, saya hanya bisa membahas seputar resep masakan."}

# --- Inisialisasi Komponen AI ---
conversational_rag_chain = None
initialization_error = None

try:
    load_dotenv()
    print("Menginisialisasi komponen AI...")
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2)
    print("Terhubung ke model Google AI")

    API_DIR = Path(__file__).parent.resolve()
    DB_PATH = str(API_DIR / "db_resep")
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    db = Chroma(persist_directory=DB_PATH, embedding_function=embedding_function)
    base_retriever = db.as_retriever(search_kwargs={"k": 2})
    retriever = MultiQueryRetriever.from_llm(retriever=base_retriever, llm=llm)

    contextualize_q_prompt = ChatPromptTemplate.from_messages([("system", "Diberikan riwayat obrolan dan pertanyaan lanjutan, tulis ulang pertanyaan tersebut menjadi pertanyaan mandiri."), MessagesPlaceholder("chat_history"), ("human", "{input}")])
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)

    qa_system_prompt = "<context>{context}</context>\n\nAnda adalah 'Chef Chimi', seorang asisten resep dari Indonesia. Gunakan HANYA informasi dari 'Konteks Resep' di atas untuk menjawab pertanyaan pengguna. Persona Anda adalah Chef Chimi. JANGAN PERNAH menyebutkan bahwa Anda adalah AI."
    qa_prompt = ChatPromptTemplate.from_messages([("system", qa_system_prompt), MessagesPlaceholder("chat_history"), ("human", "{input}")])
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    intent_prompt = ChatPromptTemplate.from_messages([("system", "Klasifikasikan input pengguna ke dalam kategori: 'SAPAAN', 'TENTANG_RESEP', 'TENTANG_DIRI', atau 'DILUAR_TOPIK'. Jawab HANYA dengan nama kategori."), MessagesPlaceholder("chat_history"), ("human", "{input}")])
    intent_chain = intent_prompt | llm | RunnableLambda(extract_intent)

    full_system_chain = RunnableBranch(
        (lambda x: "SAPAAN" in intent_chain.invoke(x), RunnableLambda(get_greeting_response)),
        (lambda x: "TENTANG_DIRI" in intent_chain.invoke(x), RunnableLambda(get_self_intro_response)),
        (lambda x: "DILUAR_TOPIK" in intent_chain.invoke(x), RunnableLambda(get_rejection_response)),
        rag_chain
    )

    chat_history_store = {}
    def get_session_history(session_id: str) -> ChatMessageHistory:
        if session_id not in chat_history_store:
            chat_history_store[session_id] = ChatMessageHistory()
        return chat_history_store[session_id]

    conversational_rag_chain = RunnableWithMessageHistory(full_system_chain, get_session_history, input_messages_key="input", history_messages_key="chat_history", output_messages_key="answer")
    print("✅ AI Chef 'Chimi' siap menerima pesanan!")

except Exception as e:
    initialization_error = f"Gagal menginisialisasi AI: {e}"
    print(f"❌ {initialization_error}")
    traceback.print_exc()

# --- Vercel Serverless Function Handler ---
class handler(BaseHTTPRequestHandler):
    
    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        if initialization_error or not conversational_rag_chain:
            error_message = initialization_error or "AI tidak berhasil diinisialisasi"
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": error_message}).encode('utf-8'))
            return

        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data)

            question = body.get('question')
            session_id = body.get('session_id')

            if not question or not session_id:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Mohon sertakan 'question' dan 'session_id'"}).encode('utf-8'))
                return

            result = conversational_rag_chain.invoke({"input": question}, config={"configurable": {"session_id": session_id}})
            answer = result.get('answer', 'Maaf, terjadi kesalahan.')

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"answer": answer}).encode('utf-8'))

        except Exception as e:
            print(f"\n--- ERROR SAAT REQUEST CHAT ---\n{traceback.format_exc()}---------------------------------")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Terjadi kesalahan: {e}"}).encode('utf-8'))