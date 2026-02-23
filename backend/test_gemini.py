import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from backend.copilot import ChatAgent

def test_gemini():
    print("--- Gemini Verification ---")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY environment variable not set.")
        return

    print("Initializing ChatAgent...")
    agent = ChatAgent()
    
    if not agent.has_gemini:
        print("ERROR: ChatAgent failed to initialize Gemini.")
        return

    print("Testing Query...")
    context = {
        "oee": {"oee": 85.5, "availability": 90, "performance": 95, "quality": 100, "trust": 0.98},
        "data": {"state_code": 1}
    }
    query = "What is the current machine status and OEE?"
    
    response = agent.process_query(query, context)
    print(f"\nQuery: {query}")
    print(f"Response: {response}")
    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    test_gemini()
