from openai import OpenAI
from dotenv import load_dotenv
from chromadb import PersistentClient
from litellm import completion
from pydantic import BaseModel, Field
from pathlib import Path
from tenacity import retry, wait_exponential

load_dotenv(override=True)

MODEL = "openai/gpt-5-mini"
#MODEL = "groq/openai/gpt-oss-120b"
DB_NAME = str(Path(__file__).parent / "preprocessed.db")
KNOWLEDGE_BASE_PATH = Path(__file__).parent / "knowledge-base"

collection_name = "docs"
embedding_model = "text-embedding-3-large"
wait = wait_exponential(multiplier=1, min=10, max=240)

openai = OpenAI()

chroma = PersistentClient(path=DB_NAME)
collection = chroma.get_or_create_collection(collection_name)


RETRIEVAL_K = 5
FINAL_K = 3

SYSTEM_PROMPT = """
    You are a knowledgeable technical assistant for Sitecore's Content Hub product. Your expertise
    lies in topics about assets in Content Hub.
    You are chatting with a user about Content Hub assets. You get your answers solely based on the documentation
    context retrieved and nothing else. 
    Your answer will be evaluated for accuracy, relevance and completeness, so make sure it only answers the question and fully answers it.
    If you don't know the answer, say so.
    If the context does not contain the answer, say that the available
    documentation does not provide enough information. Do not invent
    steps or fill gaps using general product knowledge.
    If you don't have direct answers but can provide links that may help the users, provide them in your answer as well.

    For context, here are specific extracts from the Knowledge Base that might be directly relevant to the user's question:
    {context}

    With this context, please answer the user's question. Be accurate, relevant and complete.
"""

# we will use advanced RAG techniques such as context reranking and query rewriting to improve answers.
class Result(BaseModel):
    page_content: str
    metadata: dict


class RankOrder(BaseModel):
    order: list[int] = Field(
        description="The order of relevance of chunks, from most relevant to least relevant, by chunk id number"
    )


# ========= chunks reranking ============
@retry(wait=wait)
def rerank(question, chunks):
    system_prompt = """
        You are a document re-ranker.
        You are provided with a question and a list of relevant chunks of text from a query of a knowledge base.
        The chunks are provided in the order they were retrieved; this should be approximately ordered by relevance, but you may be able to improve on that.
        You must rank order the provided chunks by relevance to the question, with the most relevant chunk first.
        Reply only with the list of ranked chunk ids, nothing else. Include all the chunk ids you are provided with, reranked.
    """
    user_prompt = f"The user has asked the following question:\n\n{question}\n\nOrder all the chunks of text by relevance to the question, from most relevant to least relevant. Include all the chunk ids you are provided with, reranked.\n\n"
    user_prompt += "Here are the chunks:\n\n"
    for index, chunk in enumerate(chunks):
        user_prompt += f"# CHUNK ID: {index + 1}:\n\n{chunk.page_content}\n\n"
    user_prompt += "Reply only with the list of ranked chunk ids, nothing else."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    response = completion(model=MODEL, messages=messages, response_format=RankOrder)
    reply = response.choices[0].message.content
    order = RankOrder.model_validate_json(reply).order
    return [chunks[i - 1] for i in order]


def make_rag_messages(question, history, chunks): #this is passed in for the reranking system prompt
    context = "\n\n".join(
        f"Extract from {chunk.metadata['source']}:\n{chunk.page_content}" for chunk in chunks
    )
    system_prompt = SYSTEM_PROMPT.format(context=context)
    return (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": question}]
    )



#=========query rewriting============
@retry(wait=wait)
def rewrite_query(question, history=[]):
    """Rewrite the user's question to be a more specific question that is more likely to surface relevant content in the Knowledge Base."""
    message = f"""
You are in a conversation with a user, answering questions about the company Insurellm.
You are about to look up information in a Knowledge Base to answer the user's question.

This is the history of your conversation so far with the user:
{history}

And this is the user's current question:
{question}

Respond only with a short, refined question that you will use to search the Knowledge Base.
It should be a VERY short specific question most likely to surface content. Focus on the question details.
IMPORTANT: Respond ONLY with the precise knowledgebase query, nothing else.
"""
    response = completion(model=MODEL, messages=[{"role": "system", "content": message}])
    return response.choices[0].message.content

#this is used to combine the result of fetching context using the original quesiton and the rewritten question.
def merge_chunks(chunks, rewrite_chunks): 
    merged = chunks[:] #creates a shallow copy of the entire chunks list and assigns it to merged
    # adding /removing stuff from merged won't change chunks
    # though items inside both lists refer to the same objects, so modifying a chunk object affects what you see thru both list
    existing = [chunk.page_content for chunk in chunks] #make a list consisting just of the chunk page_content
    for chunk in rewrite_chunks:
        if chunk.page_content not in existing:
            merged.append(chunk) #basically, if the rewritten query fetched chunks that did not come with the original query, add to the list of chunks
    return merged


# ========== fetching context =============
def fetch_context_unranked(question):
    #turn question into embedding
    query = openai.embeddings.create(model=embedding_model, input=[question]).data[0].embedding

    results = collection.query(query_embeddings=[query], n_results=RETRIEVAL_K)
    chunks = []
    for result in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append(Result(page_content=result[0], metadata=result[1]))
    return chunks

# combine the two techniques:
def fetch_context(original_question):
    rewritten_question = rewrite_query(original_question) 
    chunks1 = fetch_context_unranked(original_question)
    chunks2 = fetch_context_unranked(rewritten_question)
    chunks = merge_chunks(chunks1, chunks2)
    reranked = rerank(original_question, chunks)
    return reranked[:FINAL_K] #get only the top K after reranking

@retry(wait=wait)
def answer_question(question: str, history: list[dict] = []) -> tuple[str, list]:
    """
    Answer a question using RAG and return the answer and the retrieved context
    """
    chunks = fetch_context(question)
    messages = make_rag_messages(question, history, chunks)
    response = completion(model=MODEL, messages=messages)
    return response.choices[0].message.content, chunks  
