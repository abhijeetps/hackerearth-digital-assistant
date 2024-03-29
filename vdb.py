import requests

from bs4 import BeautifulSoup

import pinecone
from langchain_community.vectorstores import Pinecone
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFDirectoryLoader
from langchain_community.document_loaders.merge import MergedDataLoader


from consts import PINECONE_API_KEY, PINECONE_CLOUD, PINECONE_INDEX_NAME, PINECONE_DIMENSION, PINECONE_METRICS, CHUNK_OVERLAP, CHUNK_SIZE

def get_content_from_webpage(url):
    try:
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        content = soup.select('div#content').pop().get_text(separator='\n', strip=True)
        return content
    except Exception as e:
        print(f"Exception occured while trying to fetch compliance policy: #{e}")

def get_webpages_content():
    webpages = [
        'https://www.hackerearth.com/recruit/tech-recruiters/',
        'https://www.hackerearth.com/recruit/hiring-managers/',
        'https://www.hackerearth.com/recruit/university-hiring/',
        'https://www.hackerearth.com/recruit/remote-hiring/',
        'https://www.hackerearth.com/recruit/learning-and-development/'
        'https://www.hackerearth.com/recruit/pricing/'
    ]

    documents = ""
    for webpage in webpages:
        documents += get_content_from_webpage(webpage)
    return documents

def read_doc(directory="doc/"):
    file_loader = PyPDFDirectoryLoader(directory)
    documents = file_loader.load_and_split()
    return documents

def get_vector_search_index(chunks):
    embeddings = OpenAIEmbeddings()

    pinecone.init(
        api_key=PINECONE_API_KEY,
        environment=PINECONE_CLOUD
    )

    if PINECONE_INDEX_NAME in pinecone.list_indexes():
        vector_search_index = Pinecone.from_existing_index(PINECONE_INDEX_NAME, embeddings)
    else:
        pinecone.create_index(
            PINECONE_INDEX_NAME,
            dimension=PINECONE_DIMENSION,
            metric=PINECONE_METRICS
        )
        vector_search_index = Pinecone.from_documents(
            chunks,
            embeddings,
            index_name = PINECONE_INDEX_NAME
        )

    return vector_search_index

def retrieve_query(documents, query, k=4):
    index = get_vector_search_index(documents=documents)
    matching_results = index.similarity_search(query=query, k=k)
    return matching_results

def process_pdf(directory='doc/', chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    loader = PyPDFDirectoryLoader(directory)

    data = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    documents = text_splitter.split_documents(data)

    return documents

def chunk_data(documents, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function = len,
    )
    doc = text_splitter.create_documents([documents])
    return doc


def init_vdb():
    content = get_webpages_content()
    chunked_content = chunk_data(content)

    chunked_document = process_pdf()

    chunked = chunked_content + chunked_document

    index = get_vector_search_index(chunked)
    return index

init_vdb()
