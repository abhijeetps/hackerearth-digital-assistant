import json
from openai import OpenAI
import pinecone
from langchain_community.vectorstores import Pinecone
from langchain_openai import OpenAIEmbeddings

from consts import SYSTEM_MESSAGE, OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_CLOUD, PINECONE_INDEX_NAME

def get_openai_client():
    client = OpenAI(
        api_key=OPENAI_API_KEY
    )
    return client

def get_pinecone_client():
    embeddings = OpenAIEmbeddings()

    pinecone.init(
        api_key=PINECONE_API_KEY,
        environment=PINECONE_CLOUD
    )

    if PINECONE_INDEX_NAME in pinecone.list_indexes():
        vector_search_index = Pinecone.from_existing_index(PINECONE_INDEX_NAME, embeddings)
        return vector_search_index


def perform_similarity_search(query):
    vector_search_index = get_pinecone_client()
    matching_results = vector_search_index.similarity_search(query=query, k=5)
    return matching_results

def generate_prompt(similar_content, conversation, query):
    prompt = f"""
        Here's the context based between three asterisks:
        ***
        #{similar_content}
        ***

        Here's the conversation history between user and assistant:
        ```
        #{conversation[-4:]}
        ```

        Based on the context above and conversation history, answer the query separated by three pound:
        ###
        #{query}
        ###

        Answer briefly.

        #{"Ask for user's name, email and company detail. Don't ask if you already asked them from the conversation history." if len(conversation) > 4 else ""}
    """
    return prompt

def retrieve_answer(prompt, model="gpt-3.5-turbo"):
    messages = [
        {"role": "system","content": SYSTEM_MESSAGE},
        {"role": "user","content": prompt},
    ]
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            messages=messages,
            model=model,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error occured while communicating with LLM: #{e}")

def get_answer(query, conversation):
    similar_content = perform_similarity_search(query)
    prompt = generate_prompt(similar_content, conversation, query)
    answer = retrieve_answer(prompt)
    return answer

def save_data(data):
    with open(f"user_data/{data['email']}.json", "w") as file:
        file.write(json.dumps(data))

def extract_user_info(user_message, conversation_history, model="gpt-3.5-turbo"):
    print('Pikachu!')
    prompt = f"""
        Extract user's name, email, company's name and intent from in the following message separated by asterisk:
        ***
        #{user_message}
        ***

        Find the user's intention from the conversation given below between pound symbol:
        ###
            #{conversation_history}
        ###

        Return the information strictly in JSON format given below. If certain data doesn't exist, write `None`.
        $$$
        "name": "Lorem Ipsum",
        "email": "loremipsum@email.com",
        "company_name": "ABC XYZ",
        "intent": "Intention behind the user based on the conversation."
        $$$
    """

    messages = [
        {"role": "user","content": prompt},
    ]
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            messages=messages,
            model=model,
        )
        data = json.loads(response.choices[0].message.content)
        print(data)
        if data["email"]:
            save_data(data)

    except Exception as e:
        print(f"Error occured while communicating with LLM: #{e}")