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

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

from sentence_transformers import SentenceTransformer
import faiss

logger = logging.getLogger("copilot")

class ChatAgent:
    def __init__(self):
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
        
        # 1. Gemini Cloud AI (Priority)
        self.gemini_key = os.getenv("GOOGLE_API_KEY")
        self.has_gemini = False
        if HAS_GEMINI and self.gemini_key:
            try:
                genai.configure(api_key=self.gemini_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                self.has_gemini = True
                logger.info("Gemini Cloud AI initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")

        # Seed Knowledge Base
        self.add_knowledge("Machine is STOPPED when state code is 0.")
        self.add_knowledge("Machine is RUNNING when state code is 1.")
        self.add_knowledge("Machine is in FAULT when state code is 2.")
        self.add_knowledge("OEE below 50% indicates poor performance.")
        self.add_knowledge("Use the STOP button to halt production immediately.")
        self.add_knowledge("The Trust Score indicates signal quality. Low trust means sensor noise.")

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

        # Robust State Handling for Heterogeneous Machines
        state_code = sensor_data.get("state_code")
        if state_code is not None:
            state_map = {0: "STOPPED", 1: "RUNNING", 2: "FAULT"}
            current_state = state_map.get(state_code, "UNKNOWN")
            state_msg = f"Current State: {current_state} (Code {state_code})."
        else:
            state_msg = "Current State: UNKNOWN (No 'state_code' telemetry found)."

        # 3. Decision Tier: Gemini -> Heuristic/Keyword Response
        if self.has_gemini:
            return self._generate_gemini_response(query, knowledge_snippet, oee_data, sensor_data, state_msg)
        else:
            return self._generate_heuristic_response(query, knowledge_snippet, oee_data, sensor_data, state_msg)

    def _generate_gemini_response(self, query, knowledge, oee, sensors, state):
        prompt = f"""You are the Axiom Industrial Assistant.
Context: {knowledge}
Telemetry: OEE={oee.get('oee', 0)}% {state}.
Raw Data: {sensors}
Question: {query}"""
        try:
            response = self.gemini_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini Error: {e}")
            return self._generate_heuristic_response(query, knowledge, oee, sensors, state)

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
        response = f"Context: {knowledge}\n\n"
        if "status" in query.lower() or "doing" in query.lower():
            response += state
        elif "oee" in query.lower():
            if "oee" in oee:
                response += f"OEE: {oee.get('oee', 0)}%. Trust Score: {oee.get('trust', 1.0)*100:.0f}%."
            else:
                response += "OEE is not calculated for this machine."
        elif "trust" in query.lower():
             response += f"Signal Confidence: {oee.get('trust', 1.0)*100:.0f}%. "
             if oee.get('trust', 1.0) < 0.8:
                 response += "Warning: High noise detected."
        else:
            found = False
            for k, v in sensors.items():
                if k in query.lower():
                    response += f"{k}: {v}."
                    found = True
            if not found:
                response += "I'm analyzing the telemetry. Please ask about specific metrics."
        return response
