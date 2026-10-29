from pathlib import Path
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage, convert_to_messages
from langchain_core.documents import Document

from dotenv import load_dotenv


load_dotenv(override=True)

MODEL = "gpt-5-mini"
DB_NAME = str(Path(__file__).parent / "preprocessed.db")

# embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
RETRIEVAL_K = 5

SYSTEM_PROMPT = """
You are a knowledgeable technical assistant for Sitecore's Content Hub product. Your expertise
lies in topics about assets in Content Hub.
You are chatting with a user about the product.
If relevant, use the given context to answer any question.
If you don't know the answer, say so.
If you don't have direct answers but can provide links that may help the users, provide them in your answer as well.

Context:
{context}
"""

#refer to the current vector store we've built already, 
vectorstore = Chroma(persist_directory=DB_NAME, embedding_function=embeddings, collection_name="docs")
retriever = vectorstore.as_retriever()
llm = ChatOpenAI(temperature=0, model_name=MODEL)


def fetch_context(question: str) -> list[Document]:
    """
    Retrieve relevant context documents for a question.
    """
    return retriever.invoke(question, k=RETRIEVAL_K) 
    #k is a commen search_kwargs supported by most vector stores; 
    # Dictates how many documents to return (Default is usually 4).

# combine the history and the most recent message so proper context is fetched
def combined_question(question: str, history: list[dict] = []) -> str:
    """
    Combine all the user's messages into a single string.
    """
    prior = "\n".join(m["content"] for m in history if m["role"] == "user")
    return prior + "\n" + question


def answer_question(question: str, history: list[dict] = []) -> tuple[str, list[Document]]:
    """
    Answer the given question with RAG; return the answer and the context documents.
    """
    combined = combined_question(question, history)
    docs = fetch_context(combined)
    context = "\n\n".join(doc.page_content for doc in docs)
    print(f"\n\n{context}")
    system_prompt = SYSTEM_PROMPT.format(context=context)
    messages = [SystemMessage(content=system_prompt)]
    messages.extend(convert_to_messages(history))  # see note below. convert_to_messages is a langChain method
    messages.append(HumanMessage(content=question)) #"append" just add one object to the list, "extend" adds each element of a list to the list
    #if you used append and not extend for the history messages, you're gonna put the entire history as one element in the outer messages list.
    
    #print(messages)
    response = llm.invoke(messages)
    return response.content, docs #return the llm answer AND the contexts fetched

    #convert_to_messages(history): turn Gradio/chat history ([{"role": "user"|"assistant", "content": "..."}, ...]) 
    #into LangChain message objects (HumanMessage / AIMessage), then append them so the model sees prior turns.

# NOTICE: this approach is making the context fetching more relevant to the entire convo,
# but POORER when you change the topic, because you had all the context for the previous topic and 
# it can struggle to find the rel.context for the new topic