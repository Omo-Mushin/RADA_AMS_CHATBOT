"""
Core chatbot engine with query processing and LLM inference
"""

import os
import re
import tiktoken
from sentence_transformers import SentenceTransformer, CrossEncoder
from groq import Groq
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

# Configuration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
LLM_MODEL_NAME = "llama-3.3-70b-versatile"
TOP_K = 30
MAX_TOKENS = 4000

@st.cache_resource
def load_embedding_model():
    """Load and cache embedding model"""
    print(f"✅ Loading embedding model: {EMBEDDING_MODEL}")
    return SentenceTransformer(EMBEDDING_MODEL)

@st.cache_resource
def load_reranker():
    """Load and cache reranker model"""
    print(f"✅ Loading reranker model: {RERANKER_MODEL}")
    return CrossEncoder(RERANKER_MODEL)

@st.cache_resource
def init_groq_client():
    """Initialize Groq client (Python 3.13 compatible)"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("❌ GROQ_API_KEY not found in environment variables")
    
    
    client = Groq(api_key=api_key)
    print("✅ Groq client initialized")
    return client


def expand_query(query: str) -> list:
    """Generate multiple query variations for better retrieval"""
    queries = [query]
    
    # Extract well identifiers
    well_pattern = r'[A-Z]{4}\d{3}[A-Z]?:[A-Z]\d{3,4}[A-Z]?'
    wells = re.findall(well_pattern, query.upper())
    
    if wells:
        for well in wells:
            queries.append(f"well {well}")
            queries.append(f"production {well}")
    
    # Extract flowstation names
    flowstation_keywords = ['flowstation', 'fs', 'flow station']
    for keyword in flowstation_keywords:
        if keyword in query.lower():
            queries.append(query.replace(keyword, 'flowStation'))
    
    # Extract dates
    date_patterns = [
        r'\d{4}-\d{2}-\d{2}',
        r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}'
    ]
    
    for pattern in date_patterns:
        dates = re.findall(pattern, query, re.IGNORECASE)
        if dates:
            queries.append(f"date {dates[0]} production")
    
    return list(set(queries))

def limit_context(chunks, max_tokens=MAX_TOKENS, model="gpt-3.5-turbo"):
    """Limit context to max tokens"""
    try:
        enc = tiktoken.encoding_for_model(model)
    except:
        enc = tiktoken.get_encoding("cl100k_base")
    
    context, token_count = [], 0
    for chunk in chunks:
        chunk_tokens = len(enc.encode(chunk))
        if token_count + chunk_tokens > max_tokens:
            break
        context.append(chunk)
        token_count += chunk_tokens
    return context, token_count

def groq_llm_inference(groq_client, prompt: str) -> str:
    """Call Groq LLM API"""
    try:
        completion = groq_client.chat.completions.create(
            model=LLM_MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": """You are a petroleum engineering data assistant.
                    Provide accurate, specific answers based strictly on the data provided.
                    When referencing production values, always include units (barrels, Mscf, etc.).
                    When data is incomplete or missing, clearly state what's missing.
                    Format numbers with appropriate precision (2-4 decimal places).
                    Use markdown tables when presenting multiple data points."""
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_completion_tokens=1024,
            top_p=0.9,
            stream=False
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error generating response: {str(e)}"

def query_chatbot(collection, embedding_model, reranker, groq_client, 
                  user_question: str, debug=False) -> str:
    """
    Main chatbot query function
    
    Args:
        collection: ChromaDB collection
        embedding_model: SentenceTransformer model
        reranker: CrossEncoder model
        groq_client: Groq API client
        user_question: User's question
        debug: Enable debug output
    
    Returns:
        str: Generated answer
    """
    
    # Expand query for better retrieval
    expanded_queries = expand_query(user_question)
    
    if debug:
        print(f"\n🔍 Query Expansion: {expanded_queries}")
    
    # Retrieve chunks for all query variations
    all_chunks = []
    all_metadatas = []
    
    for query in expanded_queries[:3]:
        query_embedding = embedding_model.encode(query).tolist()
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=TOP_K // len(expanded_queries[:3]),
            include=["documents", "metadatas", "distances"]
        )
        
        if results["documents"] and results["documents"][0]:
            all_chunks.extend(results["documents"][0])
            all_metadatas.extend(results["metadatas"][0])
    
    if not all_chunks:
        return "❌ No relevant information found in the database for your query."
    
    # Remove duplicates
    seen = set()
    unique_chunks = []
    unique_metadatas = []
    for chunk, meta in zip(all_chunks, all_metadatas):
        if chunk not in seen:
            seen.add(chunk)
            unique_chunks.append(chunk)
            unique_metadatas.append(meta)
    
    if debug:
        print(f"\n📊 Retrieved {len(unique_chunks)} unique chunks")
    
    # Rerank chunks
    pairs = [(user_question, doc) for doc in unique_chunks]
    scores = reranker.predict(pairs)
    
    reranked_with_scores = sorted(
        zip(unique_chunks, unique_metadatas, scores),
        key=lambda x: x[2],
        reverse=True
    )
    
    reranked_chunks = [chunk for chunk, _, _ in reranked_with_scores]
    reranked_metadatas = [meta for _, meta, _ in reranked_with_scores]
    
    if debug:
        print(f"\n🎯 Top rerank score: {reranked_with_scores[0][2]:.4f}")
    
    # Limit context to max tokens
    limited_chunks, token_count = limit_context(reranked_chunks, max_tokens=MAX_TOKENS)
    
    if debug:
        print(f"\n📝 Using {len(limited_chunks)} chunks ({token_count} tokens)")
    
    # Build enriched context with metadata
    context_parts = []
    for chunk, meta in zip(limited_chunks, reranked_metadatas[:len(limited_chunks)]):
        meta_summary = f"[Collection: {meta.get('collection', 'Unknown')}]"
        if 'asset' in meta:
            meta_summary += f" [Asset: {meta['asset']}]"
        if 'flowStation' in meta or 'flowstation' in meta:
            fs = meta.get('flowStation') or meta.get('flowstation')
            meta_summary += f" [Flowstation: {fs}]"
        if 'date' in meta or 'productionDate' in meta:
            date = meta.get('date') or meta.get('productionDate')
            meta_summary += f" [Date: {date}]"
        
        context_parts.append(f"{meta_summary}\n{chunk}")
    
    context_text = "\n\n---\n\n".join(context_parts)
    
    # Construct prompt
    prompt = f"""You are analyzing petroleum engineering production data from a database.

**IMPORTANT INSTRUCTIONS:**
1. Answer based ONLY on the context provided below
2. If you find specific data, cite it with exact values and units
3. If data is missing or incomplete, clearly state what's missing
4. For production queries, include: well name, flowstation, values with units
5. For date-based queries, verify the date matches what was asked
6. If you see multiple records, analyze all of them
7. Be precise with numbers - don't round unnecessarily
8. Use markdown tables for multiple data points

**CONTEXT DATA:**
{context_text}

**USER QUESTION:**
{user_question}

**YOUR ANSWER:**"""
    
    # Get final answer from Groq LLM
    return groq_llm_inference(groq_client, prompt)
