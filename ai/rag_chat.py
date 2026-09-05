import os
import numpy as np
import pandas as pd
import streamlit as st
import snowflake.connector
from google import genai
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer

load_dotenv()

CHAT_MODEL = "gemini-3.6-flash"
NEW_REVIEWS = 500
TOK_K = 5

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
def read_reviews_from_snowflake():
    conn = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )

    query = f"""
        SELECT REVIEW_ID, CITY, RATING, COMMENT
        FROM ZOMATO.STAGING.STG_REVIEWS
        SAMPLE ({NEW_REVIEWS} ROWS)
    """
    df = conn.cursor().execute(query).fetch_pandas_all()
    conn.close()

    df.columns = [col.lower() for col in df.columns]
    return df

@st.cache_data()
def load_reviews():
    df = read_reviews_from_snowflake()
    vectorizer = TfidfVectorizer(stop_words="english", max_features=10000)
    review_vectors = vectorizer.fit_transform(
        df["comment"].fillna("").astype(str)
    )
    return df, vectorizer, review_vectors

st.title("Chat with your Zomato Reviews")
st.caption(f"Searching {NEW_REVIEWS} review, answering with {CHAT_MODEL} model")

def consine_simiarity(vec_a, vec_b):
    return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))

def find_similar_reviews(question, df):
    question_vector = vectorizer.transform([question])
    scores = (review_vectors @ question_vector.T).toarray().ravel()

    df = df.copy()
    df['score'] = scores
    return df.nlargest(TOK_K, 'score')

def ask_llm(question, top_reviews):
    conext = ""

    for _, row in top_reviews.iterrows():
        conext += f" ({row['city']}, {row['rating']} stars) {row['comment']}\n"

    system_prompt = (
        "Answer ONLY using the customer reviews provided. "
        "Be concise. If the reviews don't covert it, say so"
    )

    user_prompt = f"Questions: {question}\n\nReviews:\n{conext}"

    response = client.models.generate_content(
        model=CHAT_MODEL,
        contents=user_prompt,
        config={
            "system_instruction": system_prompt,
            "temperature": 0.2,
        },
    )
    return response.text
    
review_df, vectorizer, review_vectors = load_reviews()

question = st.text_input("Ask a question about your reviews:",
                         placeholder="e.g. What are the most common complaints about delivery?")

if question:
    top_reviews = find_similar_reviews(question, review_df)
    answer = ask_llm(question, top_reviews)

    st.markdown(f"**Answer:**")
    st.write(answer)

    with st.expander("Reviews used to build this answer"):
        st.dataframe(top_reviews[['city', 'rating', 'comment']], hide_index=True)