# -*- coding: utf-8 -*-
"""NWOai.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1xqOj_Y9UQMpKhcQJCl6wVSRWKk3huUHu
"""

#Import Json file into notebook
import json
from google.colab import files
uploaded = files.upload()

from google.cloud import bigquery
from google.oauth2 import service_account
credentials = service_account.Credentials.from_service_account_file(
'nwo-sample-5f8915fdc5ec.json')

project_id = 'nwo-sample'
client = bigquery.Client(credentials= credentials,project=project_id)

def gcp2df(sql): 
  query = client.query(sql)
  results = query.result()
  return results.to_dataframe()

query_job = """
   SELECT *
   FROM graph.tweets
   """

query = """select 
link_id, 
subreddit_id, 
subreddit, 
author, 
author_id, 
body,
created_utc
from graph.tweets
"""

#import data 
from google.colab import files
uploaded = files.upload()

import pandas as pd
import io
reddit = pd.read_csv(io.StringIO(uploaded['abt.csv'].decode('utf-8')))
reddit

#Import essential libraries 
import numpy as np # linear algebra
import spacy
import string
import gensim
import operator
import re

"""**Data Cleaning and Pre-processing**

This step is very vital in our workflow the purpose is to remove words and characters which makes readability easy but wont impact our work positively.

> Indented block


"""

#Import Stop words function to remove list of stop words in the corpa of texts that we have since they have very little or no semantic value
from spacy.lang.en.stop_words import STOP_WORDS

spacy_nlp = spacy.load('en_core_web_sm')

#create list of punctuations and stopwords
punctuations = string.punctuation
stop_words = spacy.lang.en.stop_words.STOP_WORDS

def spacy_tokenizer(sentence):
 
    #remove distracting single quotes
    sentence = re.sub('\'','',str(sentence))

    #remove digits adnd words containing digits
    sentence = re.sub('\w*\d\w*','',sentence)

    #replace extra spaces with single space
    sentence = re.sub(' +',' ',sentence)

    #remove unwanted lines starting from special charcters
    sentence = re.sub(r'\n: \'\'.*','',sentence)
    sentence = re.sub(r'\n!.*','',sentence)
    sentence = re.sub(r'^:\'\'.*','',sentence)
    
    #remove non-breaking new line characters
    sentence = re.sub(r'\n',' ',sentence)
    
    #remove punctunations
    sentence = re.sub(r'[^\w\s]',' ',sentence)
    
    #creating token object
    tokens = spacy_nlp(sentence)
    
    #lower, strip and lemmatize
    tokens = [word.lemma_.lower().strip() if word.lemma_ != "-PRON-" else word.lower_ for word in tokens]
    
    #remove stopwords, and exclude words less than 2 characters
    tokens = [word for word in tokens if word not in stop_words and word not in punctuations and len(word) > 2]
    
    #return tokens
    return tokens

# Commented out IPython magic to ensure Python compatibility.
print ('Cleaning and Tokenizing...')
# %time reddit['body_tokenized'] = reddit['body'].map(lambda x: spacy_tokenizer(x))

reddit.head()

"""**Build A word dictionary**

The purpose of this step is to assign unique words an ID and store their frequencies 
"""

#Processing this data was quite tasking had to reduce row count a couple of times 
#to fasten processing in future time lets store the tokenized column to a separate variable 
token_reddit = reddit['body_tokenized']
token_reddit[0:10]

# Commented out IPython magic to ensure Python compatibility.
from gensim import corpora

#creating term dictionary
# %time dictionary = corpora.Dictionary(token_reddit)


#list of few which which can be further removed
stoplist = set('hello also again or and if this can would should could tell ask stop come go')
stop_ids = [dictionary.token2id[stopword] for stopword in stoplist if stopword in dictionary.token2id]
dictionary.filter_tokens(stop_ids)

#print top 100 items from the dictionary with their unique token-id
dict_tokens = [[[dictionary[key], dictionary.token2id[dictionary[key]]] for key, value in dictionary.items() if key <= 100]]
print (dict_tokens)

"""**Create a BOW model**

The purpose of this action is to extract features from our text that are essential for modelling.
"""

corpus = [dictionary.doc2bow(desc) for desc in token_reddit]

word_frequencies = [[(dictionary[id], frequency) for id, frequency in line] for line in corpus[0:3]]

print(word_frequencies)

"""**Build a TF-IDF and LSI model **

Term frequency-Inverse Document Frequency explores the corpa of texts and uses cosine similarity to determine the most important words in each document, afterwards we pass the results to the LSI model and specify the number of features to build.
"""

# Commented out IPython magic to ensure Python compatibility.
# %time reddit_tfidf_model = gensim.models.TfidfModel(corpus, id2word=dictionary)
# %time reddit_lsi_model = gensim.models.LsiModel(reddit_tfidf_model[corpus], id2word=dictionary, num_topics=500)

# Commented out IPython magic to ensure Python compatibility.
#Serialize and Store the corpus locally for easy retrival whenver required.
# %time gensim.corpora.MmCorpus.serialize('reddit_tfidf_model_mm', reddit_tfidf_model[corpus])
# %time gensim.corpora.MmCorpus.serialize('reddit_lsi_model_mm',reddit_lsi_model[reddit_tfidf_model[corpus]])

#Load the indexed corpus
reddit_tfidf_corpus = gensim.corpora.MmCorpus('reddit_tfidf_model_mm')
reddit_lsi_corpus = gensim.corpora.MmCorpus('reddit_lsi_model_mm')

print(reddit_tfidf_corpus)
print(reddit_lsi_corpus)

# Commented out IPython magic to ensure Python compatibility.
from gensim.similarities import MatrixSimilarity

# %time reddit_index = MatrixSimilarity(reddit_lsi_corpus, num_features = reddit_lsi_corpus.num_terms)

"""**SEMANTIC SEARCH**

We have words from our reddit posts initialized and loaded, we can identify similar terms. 
We will input a search query and model will return relevant terms  with "Relevance %" which is the similarity score. The higher the similarity score, the more similar the query to the documetn at the given index. 
"""

from operator import itemgetter

def search_similar_terms(search_term):

    query_bow = dictionary.doc2bow(spacy_tokenizer(search_term))
    query_tfidf = reddit_tfidf_model[query_bow]
    query_lsi = reddit_lsi_model[query_tfidf]

    reddit_index.num_best = 20

    reddit_list = reddit_index[query_lsi]

    reddit_list.sort(key=itemgetter(1), reverse=True)
    reddit_names = []

    for j, red in enumerate(reddit_list):

        reddit_names.append (
            {
                'Relevance': round((red[1] * 100),2),
                'Body': reddit['body'][red[0]],
             'Subreddit': reddit['subreddit'][red[0]]
             
                
            }

        )
        if j == (reddit_index.num_best-1):
            break

    return pd.DataFrame(reddit_names, columns=['Relevance','Body', 'Subreddit'])

# search for redit terms that are related to below search parameters
search_similar_terms('Biden')

# search for redit terms that are related to below search parameters
search_similar_terms('perfume')

# search for redit terms that are related to below search parameters
search_similar_terms('vaccine')