from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from retrieval.retrieve import get_retriever

def main():
    print("Initializing LLM (Ollama - mistral)...")
    # Initialize the local LLM
    try:
        llm = Ollama(model="mistral")
    except Exception as e:
        print(f"Error initializing Ollama: {e}")
        print("Please ensure Ollama is installed and running, and the mistral model is downloaded.")
        return

    print("Loading Retriever...")
    try:
        retriever = get_retriever()
    except Exception as e:
        print(f"Error loading retriever: {e}")
        print("Have you ingested any documents yet? Run 'python -m ingestion.ingest' first.")
        return

    print("Building RAG Chain...")
    prompt = PromptTemplate.from_template(
        "You are an expert assistant. Use the following retrieved context to answer the user's question accurately. "
        "If the answer cannot be found in the context, explicitly state that you don't know. Do not make up information.\n\n"
        "### Context:\n{context}\n\n"
        "### Question:\n{question}\n\n"
        "### Answer:\n"
    )

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    qa_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    print("\n" + "="*50)
    print("🤖 Local RAG System Ready!")
    print("Type 'exit' or 'quit' to stop.")
    print("="*50 + "\n")

    while True:
        query = input("\nQ: ")
        
        if query.lower() in ['exit', 'quit']:
            print("Exiting...")
            break
            
        if not query.strip():
            continue
            
        print("Thinking...")
        try:
            print("\nA: ", end="", flush=True)
            for chunk in qa_chain.stream(query):
                print(chunk, end="", flush=True)
            print()
        except Exception as e:
            print(f"\nError generating response: {e}")

if __name__ == "__main__":
    main()
