# mocks/openai_stub.py
def generate_response(prompt):
    # Stubbed response to avoid external calls in dev
    return {
        'text': '<<STUBBED LLM RESPONSE - enable real LLM with ENABLE_LLM=true and KeyVault secrets>>',
        'metadata': {'stub': True}
    }
