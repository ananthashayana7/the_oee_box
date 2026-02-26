import logging
import random
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import os
import google.generativeai as genai

logger = logging.getLogger("copilot")

class ChatAgent:
    def __init__(self):
        logger.info("Initializing Semantic Agent (RAG + Gemini)...")
        # RAG (Local)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = 384
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents = []

        # Gemini (Cloud)
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
            self.llm = genai.GenerativeModel('gemini-pro')
            logger.info("Gemini API Configured.")
        else:
            self.llm = None
            logger.warning("GEMINI_API_KEY not found. Fallback to heuristic mode.")

        # Seed Knowledge Base
        self.add_knowledge("Machine is STOPPED when state code is 0.")
        self.add_knowledge("Machine is RUNNING when state code is 1.")
        self.add_knowledge("Machine is in FAULT when state code is 2.")
        self.add_knowledge("OEE below 50% indicates poor performance.")
        self.add_knowledge("Use the STOP button to halt production immediately.")
        self.add_knowledge("The Trust Score indicates signal quality. Low trust means sensor noise.")

    def add_knowledge(self, text):
        embedding = self.model.encode([text])
        self.index.add(np.array(embedding, dtype=np.float32))
        self.documents.append(text)

    def process_query(self, query: str, context: dict) -> str:
        """
        Semantic RAG: Embed query, find relevant docs, augment response via Gemini.
        """
        # 1. Retrieve Knowledge
        q_embed = self.model.encode([query])
        D, I = self.index.search(np.array(q_embed, dtype=np.float32), k=2)

        retrieved_context = [self.documents[i] for i in I[0] if i < len(self.documents)]
        knowledge_snippet = " ".join(retrieved_context)

        # 2. Extract Real-Time Context
        oee_data = context.get("oee", {})
        sensor_data = context.get("data", {})

        # Robust State Handling for Heterogeneous Machines
        state_code = sensor_data.get("state_code")
        state_str = "UNKNOWN"
        if state_code is not None:
            state_map = {0: "STOPPED", 1: "RUNNING", 2: "FAULT"}
            state_str = state_map.get(state_code, f"CODE_{state_code}")

        # Construct Prompt
        prompt = f"""
        You are an industrial expert AI assisting an operator.

        Context (Knowledge Base):
        {knowledge_snippet}

        Live Machine Telemetry:
        - Machine State: {state_str}
        - OEE: {oee_data.get('oee', 'N/A')}%
        - Full Sensor Data: {sensor_data}

        User Query: "{query}"

        Instructions:
        - Answer concisely based on the telemetry and context.
        - If the state is unknown or data is missing, explain why.
        - Be professional and safety-conscious.
        """

        # 3. Generate Response
        if self.llm:
            try:
                response = self.llm.generate_content(prompt)
                return response.text
            except Exception as e:
                logger.error(f"Gemini API Error: {e}")
                return f"AI Error: {e}. Fallback: Machine State is {state_str}."

        # 4. Fallback Heuristics (No API Key)
        response = f"Context: {knowledge_snippet}\n\n"
        if "status" in query.lower():
            response += f"Current State: {state_str}."
        elif "oee" in query.lower():
            if "oee" in oee_data:
                response += f"OEE: {oee_data.get('oee', 0)}%."
            else:
                response += "OEE not calculated."
        else:
            response += f"Sensors: {sensor_data}"

        return response
