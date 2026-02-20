import logging
import random
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

logger = logging.getLogger("copilot")

class ChatAgent:
    def __init__(self):
        logger.info("Initializing Semantic Agent (RAG)...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = 384
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents = []

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
        Semantic RAG: Embed query, find relevant docs, augment response.
        """
        # 1. Retrieve Knowledge
        q_embed = self.model.encode([query])
        D, I = self.index.search(np.array(q_embed, dtype=np.float32), k=2)

        retrieved_context = [self.documents[i] for i in I[0] if i < len(self.documents)]
        knowledge_snippet = " ".join(retrieved_context)

        # 2. Extract Real-Time Context
        oee_data = context.get("oee", {})
        sensor_data = context.get("data", {})
        state_code = sensor_data.get("state_code", 0)
        state_map = {0: "STOPPED", 1: "RUNNING", 2: "FAULT"}
        current_state = state_map.get(state_code, "UNKNOWN")

        # 3. Heuristic Generation (Mocking LLM generation for speed)
        # In a real app, we would feed `knowledge_snippet` + `context` into Llama/GPT.

        response = f"Context: {knowledge_snippet}\n\n"

        if "status" in query.lower() or "doing" in query.lower():
            response += f"Current State: {current_state} (Code {state_code})."
        elif "oee" in query.lower():
            response += f"OEE: {oee_data.get('oee', 0)}%. Trust Score: {oee_data.get('trust', 1.0)*100:.0f}%."
        elif "trust" in query.lower():
             response += f"Signal Confidence: {oee_data.get('trust', 1.0)*100:.0f}%. "
             if oee_data.get('trust', 1.0) < 0.8:
                 response += "Warning: High noise detected."
        else:
            # Generic sensor lookup
            found = False
            for k, v in sensor_data.items():
                if k in query.lower():
                    response += f"{k}: {v}."
                    found = True
            if not found:
                response += "I'm analyzing the telemetry. Please ask about specific metrics."

        return response
