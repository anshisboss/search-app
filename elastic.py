import re
import streamlit as st
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
import rasa 
import requests
from mapp import es
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk
import asyncio
from rasa.core.agent import Agent
nltk.download('punkt')
nltk.download('stopwords')
from nltk.stem import PorterStemmer

@st.cache(allow_output_mutation=True)
def connect_to_elasticsearch():
  
  try:
    es = Elasticsearch(['http://localhost:9200'])
    # print("Successfully connected to Elasticsearch.")
    return es
  except Exception as e:
    print(f"Failed to connect to Elasticsearch: {e}")
    return None
  
rasa_server_url = "http://localhost:5005/webhooks/rest/webhook"

class Model:

    def __init__(self, model_path: str) -> None:
        self.agent = Agent.load(model_path)
        print("NLU model loaded")


    def message(self, message: str) -> str:
        message = message.strip()
        result = asyncio.run(self.agent.parse_message(message))
        return result


def printres(results,brand,category,myset):
    count = 0
    if brand and category:
        for result in results:
            
            if count == 26 : break
            if( result['_source']['secondary_category'].lower()!=category.lower().strip() or result['_source']['br_nm'].lower()!=brand.lower().strip()): continue
            count += 1
            myset.add(result['_source']['fullName'])
            with st.container():
                    if '_source' in result:
                        try:
                            st.header(f"{result['_source']['fullName']}")
                        except Exception as e:
                            print(e)
                        
                        try:
                            st.write(f"Description: I am a result of filtering both brand and category")
                        except Exception as e:
                            print(e)
                        try:
                            st.write(f"Brand: {result['_source']['br_nm']}")
                        except Exception as e:
                            print(e)
                        try:
                            st.write(f"Category: {result['_source']['secondary_category']}")
                        except Exception as e:
                            print(e)
                        st.divider()
    if brand:
        for result in results:
            if count == 26 : break
            if(result['_source']['br_nm'].lower()!=brand.lower().strip()): continue
            
            if result['_source']['fullName'] not in myset:
                with st.container():
                    if '_source' in result:
                        try:
                            st.header(f"{result['_source']['fullName']}")
                        except Exception as e:
                            print(e)
                        
                        try:
                            st.write(f"Description: I am a result of filtering  brand ")
                        except Exception as e:
                            print(e)
                        try:
                            st.write(f"Brand: {result['_source']['br_nm']}")
                        except Exception as e:
                            print(e)
                        try:
                            st.write(f"Category: {result['_source']['secondary_category']}")
                        except Exception as e:
                            print(e)
                        st.divider()
                myset.add(result['_source']['fullName'])
                count += 1
    if category:
        for result in results:
            if count == 26 : break
            if(result['_source']['secondary_category'].lower()!=category.lower().strip()): continue
            if result['_source']['fullName'] not in myset:
                with st.container():
                    if '_source' in result:
                        try:
                            st.header(f"{result['_source']['fullName']}")
                        except Exception as e:
                            print(e)
                        
                        try:
                            st.write(f"Description: I am a result of filtering category ")
                        except Exception as e:
                            print(e)
                        try:
                            st.write(f"Brand: {result['_source']['br_nm']}")
                        except Exception as e:
                            print(e)
                        try:
                            st.write(f"Category: {result['_source']['secondary_category']}")
                        except Exception as e:
                            print(e)
                        st.divider()
                myset.add(result['_source']['fullName'])
                count += 1
    for result in results:
        if count == 26 : break 
        if result['_source']['fullName'] not in myset:
                with st.container():
                    if '_source' in result:
                        try:
                            st.header(f"{result['_source']['fullName']}")
                        except Exception as e:
                            print(e)
                        
                        try:
                            st.write(f"Description: {result['_source']['search_text']}")
                        except Exception as e:
                            print(e)
                        try:
                            st.write(f"Brand: {result['_source']['br_nm']}")
                        except Exception as e:
                            print(e)
                        try:
                            st.write(f"Category: {result['_source']['secondary_category']}")
                        except Exception as e:
                            print(e)
                        st.divider()
                myset.add(result['_source']['fullName'])
                count += 1

def entity(query):
    
    payload_data = {
        "sender": "user123",
        "message": query
    }

    response = requests.post(rasa_server_url, json=payload_data)

    
    if response.status_code == 200:
        
        rasa_response = response.json()
        
        
        if rasa_response and len(rasa_response) > 0:
            bot_message = rasa_response[0].get('text', "No response received from Rasa.")

            print("Response from Rasa:", bot_message)
            return  bot_message
        else:
            print("No response received from Rasa.")
    else:
        print("Error:", response.status_code)

indexName = "hkdata1"


def search(input_keyword):
    es = connect_to_elasticsearch()
    
    query = {
        "query" : {
            "multi_match": {
                "query": input_keyword,
                "fields": ["fullName", "search_text", "br_nm"],
                "minimum_should_match": "90%"
            }
        }
    }
    
    
    res = es.search(index="hkdata1", body=query, size=200)
    results = res["hits"]["hits"]

    return results

def context_search(input_keyword):
    
    model = SentenceTransformer('all-mpnet-base-v2')
    vector_of_input_keyword = model.encode(input_keyword)

    
    query = {
            "field": "embeddings",
            "query_vector": vector_of_input_keyword,
            "k": 500,
            "num_candidates": 1000
        }
    res = es.knn_search(index="hkdata1"
                            , knn=query 
                            , source=["fullName","search_text","br_nm","secondary_category"]
                            )
    results = res["hits"]["hits"]

    return results

def fuzzy_search(input_keyword):

    query = {
        "query" : {
            "multi_match": {
                "query": input_keyword,
                "fields": ["fullName", "search_text", "br_nm"],
                "fuzziness": 2
            }
        }
    }
    
    
    res = es.search(index="hkdata1", body=query, size=200)
    results = res["hits"]["hits"]

    return results

def preprocess_text(text):
    
    text = text.lower()

    words = word_tokenize(text)

    stop_words = set(stopwords.words('english'))
    stop_words.add('best')
    stop_words.add('wanna')
    stop_words.remove('on')

    filtered_words = [word for word in words if word not in stop_words]

    return " ".join(filtered_words)


def main():
    st.title("Search at HealthKart")

    query = st.text_input("Enter your search query")
    

    if st.button("Search"):

        text = entity(query)
        
        
        brand_match = ""
        category_match = ""

        words = [word.strip() for word in text.split() if word.strip()]

        for i in range(len(words)):
            if i == len(words) : break
            if  words[i] == 'brand':
                i += 1
                while i<len(words) and words[i]!='and':
                    brand_match += words[i]+ " "
                    i+=1
            if i == len(words): break 
            if  words[i] == 'category':
                i += 1
                while i < len(words) :
                    category_match+=words[i]+ " "
                    i+=1
        
        
        brand = None
        category = None

        
        if brand_match and brand_match!='none':
            brand = brand_match
        if category_match and category_match!='none':
            category = category_match

          

        if(category == 'category ') : category = 'proteins'

        if brand : 
            query += " " + brand

        if brand == 'Optimum Nutrition ' :
            brand = 'on'
        
        results = search(query)
        more_results = context_search(query)

        print(brand)
        print(category)

        print(query)

        st.subheader("Search Results")
    
        myset = set()

        printres(results,brand,category,myset)

        if len(results) == 0:
            print('running fuzzy query')
            results = fuzzy_search(query)
            printres(results,brand,category,myset)    
        
        st.subheader("more Results")
        
        more_results = context_search(query)

        printres(more_results,brand,category,myset)

    
if __name__ == "__main__":
    main()
