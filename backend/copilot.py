import logging
import random
import numpy as np
import os
import requests
import ssl

# Globally disable SSL verification for corporate proxies
ssl._create_default_https_context = ssl._create_unverified_context
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['HF_HUB_DISABLE_SSL_VERIFY'] = '1'

from sentence_transformers import SentenceTransformer
import faiss
try:
    from llama_cpp import Llama
    HAS_LLAMA = True
except ImportError:
    HAS_LLAMA = False

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

logger = logging.getLogger("copilot")

class ChatAgent:
    def __init__(self, model_path="models/llama-3-8b-instruct.Q4_K_M.gguf"):
        logger.info("Initializing Semantic Agent (RAG)...")
        
        # 0. Initialize Embeddings with Fallback
        self.model = None
        self.index = None
        self.documents = []
        
        try:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.dimension = 384
            self.index = faiss.IndexFlatL2(self.dimension)
            logger.info("SentenceTransformer model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer (SSL/Proxy issue likely): {e}")
            logger.warning("Falling back to Heuristic Knowledge Retrieval.")
            # self.model and self.index remain None
        
        # LLM Backends
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
        self.gemini_key = os.getenv("GOOGLE_API_KEY")
        self.llm_local = None
        
        # 1. Check for Gemini (Priority)
        self.has_gemini = False
        if HAS_GEMINI and self.gemini_key:
            try:
                genai.configure(api_key=self.gemini_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                self.has_gemini = True
                logger.info("Gemini Cloud AI initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")

        # 2. Check for Ollama Connectivity
        self.has_ollama = self._check_ollama()
        if self.has_ollama:
            logger.info(f"Ollama detected at {self.ollama_host}. Using Ollama as secondary backend.")
        
        # 3. Fallback to Local Llama (llama-cpp)
        if not self.has_gemini and not self.has_ollama and HAS_LLAMA:
            if os.path.exists(model_path):
                logger.info(f"Loading local LLM from {model_path}...")
                self.llm_local = Llama(model_path=model_path, n_ctx=2048, verbose=False)
            else:
                logger.warning(f"Ollama/Gemini not found and local model missing at {model_path}.")

        # Seed Knowledge Base
        self.add_knowledge("Machine is STOPPED when state code is 0.")
        self.add_knowledge("Machine is RUNNING when state code is 1.")
        self.add_knowledge("Machine is in FAULT when state code is 2.")
        self.add_knowledge("OEE below 50% indicates poor performance.")
        self.add_knowledge("Use the STOP button to halt production immediately.")
        self.add_knowledge("The Trust Score indicates signal quality. Low trust means sensor noise.")

    def _check_ollama(self):
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False

    def add_knowledge(self, text):
        if self.model and self.index is not None:
            embedding = self.model.encode([text])
            self.index.add(np.array(embedding, dtype=np.float32))
        self.documents.append(text)

    def process_query(self, query: str, context: dict) -> str:
        """
        Semantic RAG: Embed query, find relevant docs, augment response.
        """
        # 1. Retrieve Knowledge
        knowledge_snippet = ""
        if self.model and self.index:
            try:
                q_embed = self.model.encode([query])
                D, I = self.index.search(np.array(q_embed, dtype=np.float32), k=2)
                retrieved_context = [self.documents[i] for i in I[0] if i < len(self.documents)]
                knowledge_snippet = " ".join(retrieved_context)
            except Exception as e:
                logger.error(f"Knowledge Retrieval Error: {e}")
                knowledge_snippet = self._heuristic_knowledge_retrieval(query)
        else:
            knowledge_snippet = self._heuristic_knowledge_retrieval(query)

        # 2. Extract Real-Time Context
        oee_data = context.get("oee", {})
        sensor_data = context.get("data", {})
        state_code = sensor_data.get("state_code", 0)
        state_map = {0: "STOPPED", 1: "RUNNING", 2: "FAULT"}
        current_state = state_map.get(state_code, "UNKNOWN")

        # 3. Decision Tier: Gemini -> Ollama -> Llama-cpp -> Heuristic
        if self.has_gemini:
            return self._generate_gemini_response(query, knowledge_snippet, oee_data, sensor_data, current_state)
        elif self.has_ollama:
            return self._generate_ollama_response(query, knowledge_snippet, oee_data, sensor_data, current_state)
        elif self.llm_local:
            return self._generate_llm_response(query, knowledge_snippet, oee_data, sensor_data, current_state)
        else:
            return self._generate_heuristic_response(query, knowledge_snippet, oee_data, sensor_data, current_state)

    def _generate_gemini_response(self, query, knowledge, oee, sensors, state):
        prompt = f"""You are the Axiom Industrial Assistant.
Context: {knowledge}
Telemetry: OEE={oee.get('oee')}% State={state}.
Question: {query}"""
        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini Error: {e}")
            return self._generate_heuristic_response(query, knowledge, oee, sensors, state)

    def _generate_ollama_response(self, query, knowledge, oee, sensors, state):
        prompt = f"You are the Axiom Industrial Assistant. Use the context and telemetry to answer concisely.\nContext: {knowledge}\nTelemetry: OEE={oee.get('oee')}% State={state}. Question: {query}"
        try:
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": "llama3",
                    "prompt": prompt,
                    "stream": False,
                    "system": "You are a professional industrial OEE monitoring assistant."
                },
                timeout=10
            )
            return response.json().get("response", "Internal AI Error").strip()
        except Exception as e:
            logger.error(f"Ollama Error: {e}")
            return self._generate_heuristic_response(query, knowledge, oee, sensors, state)

    def _generate_llm_response(self, query, knowledge, oee, sensors, state):
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are the Axiom Industrial Assistant. Use the following context and telemetry to answer the user query accurately and concisely.

Context: {knowledge}
Real-Time Telemetry: OEE={oee.get('oee')}% (A:{oee.get('availability')}%, P:{oee.get('performance')}%, Q:{oee.get('quality')}%). Trust: {oee.get('trust', 1.0)*100:.0f}%.
Current Machine State: {state}
Active Sensors: {list(sensors.keys())}
<|eot_id|><|start_header_id|>user<|end_header_id|>
{query}
<|end_header_id|>
<|start_header_id|>assistant<|end_header_id|>"""
        
        output = self.llm_local(prompt, max_tokens=150, stop=["<|eot_id|>"])
        return output["choices"][0]["text"].strip()

    def _heuristic_knowledge_retrieval(self, query):
        """Simple keyword matching fallback for knowledge base."""
        query_words = set(query.lower().split())
        best_matches = []
        for doc in self.documents:
            doc_words = set(doc.lower().split())
            if query_words & doc_words:
                best_matches.append(doc)
        return " ".join(best_matches[:2])

    def _generate_heuristic_response(self, query, knowledge, oee, sensors, state):
        response = f"Context (Heuristic): {knowledge}\n\n"
        if "status" in query.lower() or "doing" in query.lower():
            response += f"Current State: {state}."
        elif "oee" in query.lower():
            response += f"OEE: {oee.get('oee', 0)}%. Trust: {oee.get('trust', 1.0)*100:.0f}%."
        else:
            response += "System is healthy. I'm monitoring the telemetry."
        return response
