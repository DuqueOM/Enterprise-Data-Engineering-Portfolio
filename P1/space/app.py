
import gradio as gr
import pickle
from sentence_transformers import SentenceTransformer
import faiss
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

INDEX_DIR = "indexes"
EMBED_MODEL = "sentence-transformers/all-mpnet-base-v2"
LLM_MODEL = "google/flan-t5-base"

index = faiss.read_index(f"{INDEX_DIR}/faiss.index")
metas = pickle.load(open(f"{INDEX_DIR}/metas.pkl","rb"))
embed_model = SentenceTransformer(EMBED_MODEL)
tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL)
model = AutoModelForSeq2SeqLM.from_pretrained(LLM_MODEL)

def retrieve(query, k=5):
    emb = embed_model.encode([query], convert_to_numpy=True)
    import numpy as np
    faiss.normalize_L2(emb)
    D, I = index.search(emb, k)
    snippets = []
    for i in I[0]:
        meta = metas[i]
        snippets.append({"title": meta.get("title",""), "url": meta.get("url","")})
    return snippets

def answer(query, mode="RAG", k=5):
    snippets = retrieve(query, k)
    context = "\\n\\n".join([s["title"] + " — " + s["url"] for s in snippets])
    if mode == "RAG":
        prompt = f"Responde en español con pasos claros y cita las fuentes con sus URLs.\\nContexto: {context}\\nPregunta: {query}"
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
        out = model.generate(**inputs, max_length=256)
        text = tokenizer.decode(out[0], skip_special_tokens=True)
    else:
        text = "Modo FT no implementado en demo."
    return text, [[s["title"], s["url"]] for s in snippets]

with gr.Blocks() as demo:
    gr.Markdown("# Asistente PYME — Demo")
    with gr.Row():
        inp = gr.Textbox(label="Pregunta", lines=2)
        mode = gr.Radio(["RAG","FT"], value="RAG", label="Modo")
        btn = gr.Button("Preguntar")
    out = gr.Textbox(label="Respuesta", lines=6)
    src = gr.Dataframe(headers=["title","url"], label="Fuentes (top-k)")
    btn.click(fn=answer, inputs=[inp, mode], outputs=[out, src])

if __name__ == '__main__':
    demo.launch()
