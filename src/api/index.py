import os
import traceback
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    load_dotenv()
    print("Menginisialisasi komponen AI...")

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.2
    )
    print("Terhubung ke model di LM Studio")

    # --- Inisialisasi komponen RAG lainnya ---
    API_DIR = Path(__file__).parent.resolve()
    DB_PATH = str(API_DIR / "db_resep")
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    db = Chroma(persist_directory=DB_PATH, embedding_function=embedding_function)
    base_retriever = db.as_retriever(search_kwargs={"k": 2})
    retriever = MultiQueryRetriever.from_llm(retriever=base_retriever, llm=llm)

    # --- 2. BUAT RAG CHAIN UTAMA (seperti sebelumnya) ---
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", "Diberikan riwayat obrolan dan pertanyaan lanjutan, tulis ulang pertanyaan tersebut menjadi pertanyaan mandiri."),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)

    qa_system_prompt = """
    Anda adalah 'Chef Chimi', seorang asisten resep dari Indonesia.
    Gunakan HANYA informasi dari 'Konteks Resep' di bawah ini untuk menjawab pertanyaan pengguna dengan lengkap dan ramah.
    JANGAN PERNAH menyebutkan bahwa Anda adalah model bahasa atau AI. Persona Anda adalah Chef Chimi.

    <context>
    {context}
    </context>
    """
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    
    # --- 3. BUAT "PENJAGA GERBANG" DENGAN KATEGORI  ---
    intent_prompt = ChatPromptTemplate.from_messages([
        ("system", """
        Anda adalah classifier yang sangat akurat. Klasifikasikan pertanyaan terakhir pengguna ('input') berdasarkan riwayat obrolan ('chat_history') ke dalam salah satu dari empat kategori berikut: 'SAPAAN', 'TENTANG_RESEP', 'TENTANG_DIRI', atau 'DILUAR_TOPIK'.
        Jawab HANYA dengan salah satu dari empat kategori tersebut, tanpa penjelasan apa pun.

        --- CONTOH ---
        Pertanyaan: halo,hello,hai,helo
        Kategori: SAPAAN

        Pertanyaan: terima kasih banyak
        Kategori: SAPAAN

        Pertanyaan: siapa kamu?
        Kategori: TENTANG_DIRI

        Pertanyaan: apa yang bisa kamu lakukan
        Kategori: TENTANG_DIRI

        Pertanyaan: carikan resep ayam goreng
        Kategori: TENTANG_RESEP

        Pertanyaan: bagaimana cara membuat nasi goreng?
        Kategori: TENTANG_RESEP

        Pertanyaan: apa itu pemrograman?
        Kategori: DILUAR_TOPIK

        Pertanyaan: tolong buatkan saya file html
        Kategori: DILUAR_TOPIK
         
        
        """),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    intent_chain = intent_prompt | llm | RunnableLambda(lambda x: x.content.strip())

    # --- 4. GABUNGKAN SEMUANYA DENGAN LOGIKA 4 PERCABANGAN ---
    greeting_chain = RunnableLambda(
        lambda x: {"answer": "Halo! Saya Chef Chimi, asisten resep virtual Anda. Ada yang bisa saya bantu?"}
    )
    self_intro_chain = RunnableLambda(
        lambda x: {"answer": "Saya Chef Chimi! Saya siap membantu Anda menemukan resep masakan Indonesia dari database saya."}
    )
    rejection_chain = RunnableLambda(
        lambda x: {"answer": "Maaf, sebagai Chef Chimi, saya hanya bisa membahas seputar resep masakan."}
    )

    def route(info):
        intent = intent_chain.invoke(info)
        if "SAPAAN" in intent:
            return greeting_chain
        elif "TENTANG_DIRI" in intent:
            return self_intro_chain
        elif "DILUAR_TOPIK" in intent:
            return rejection_chain
        else: 
            return rag_chain

    full_system_chain = RunnableLambda(route)

    # --- 5. Tambahkan Memori ke Sistem Final ---
    chat_history_store = {}
    def get_session_history(session_id: str) -> ChatMessageHistory:
        if session_id not in chat_history_store:
            chat_history_store[session_id] = ChatMessageHistory()
        return chat_history_store[session_id]

    conversational_rag_chain = RunnableWithMessageHistory(
        full_system_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )
    print("✅ AI Chef 'Chimi' (V4.9) siap menerima pesanan!")

except Exception as e:
    print(f" Gagal menginisialisasi AI: {e}")
    traceback.print_exc()
    conversational_rag_chain = None

class ChatRequest(BaseModel):
    question: str
    session_id: str

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    if not conversational_rag_chain:
        return JSONResponse(status_code=500, content={"error": "AI tidak berhasil diinisialisasi"})

    try:
        async def stream_generator():
            full_response = ""
            async for chunk in conversational_rag_chain.astream(
                {"input": request.question},
                config={"configurable": {"session_id": request.session_id}}
            ):
                if answer_chunk := chunk.get("answer"):
                    full_response += answer_chunk
                    yield answer_chunk
        
        return StreamingResponse(stream_generator(), media_type="text/event-stream")

    except Exception as e:
        print("\n--- ERROR SAAT REQUEST CHAT ---")
        traceback.print_exc()
        print("---------------------------------")
        return JSONResponse(status_code=500, content={"error": f"Terjadi kesalahan saat memproses permintaan: {e}"})

