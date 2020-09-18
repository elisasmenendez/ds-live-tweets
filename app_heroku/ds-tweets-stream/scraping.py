# import sqlite3
import os
import psycopg2

import pandas as pd
import keys 
import settings
import tweepy
import pickle
import string
import re
from sklearn.feature_extraction.text import CountVectorizer
import nltk
nltk.download('stopwords')
nltk.download('punkt')
from nltk.tokenize import word_tokenize

# A few queries to use along this process
drop_query = "DROP TABLE IF EXISTS {}".format(settings.TABLE_NAME)
create_query = "CREATE TABLE IF NOT EXISTS {} (id VARCHAR(255), time TIMESTAMP, tweet VARCHAR(255), sentiment INT, topic VARCHAR(255))".format(settings.TABLE_NAME)
insert_query = "INSERT INTO {} (id, time, tweet, sentiment, topic) VALUES (%s, %s, %s, %s, %s)".format(settings.TABLE_NAME)
delete_query = '''
DELETE FROM {0}
WHERE id IN (SELECT id FROM {0}
            ORDER BY time asc
            LIMIT 10 ) AND
    (SELECT COUNT(*) FROM {0}) > 110
'''.format(settings.TABLE_NAME)

# Import the vectorizer and the classifier
vectorizer_sav = pickle.load(open('vectorizer.sav', 'rb'))
classifier_sav = pickle.load(open('classifier_regression.sav', 'rb'))

# Set the database to store the streamed tweets
DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
c = conn.cursor()

# Create tables
c.execute(drop_query)
conn.commit()
c.execute(create_query)
conn.commit()

# Get the topic of the tweet (participant name or a general topic)
def get_topic(tweet):
    tokens = word_tokenize(tweet)
    topic = []
    if 'jojo' in tokens or 'todynho' in tokens:
        topic.append('Jojo Todynho')
    if 'raissa' in tokens:
        topic.append('Raissa')
    if 'mirella' in tokens:
        topic.append('MC Mirella')
    if 'jake' in tokens:
        topic.append('Jakelyne')
    if 'stefani' in tokens:
        topic.append('Stefani')
    if 'luiza' in tokens:
        topic.append('Luiza')
    if 'carol' in tokens or 'narizinho' in tokens:
        topic.append('Narizinho')
    if 'victoria' in tokens:
        topic.append('Victoria')
    if 'lidi' in tokens:
        topic.append('Lidi Lisboa')
    if 'jp' in tokens:
        topic.append('JP Gadêlha')
    if 'biel' in tokens:
        topic.append('Biel')
    if 'lipe' in tokens:
        topic.append('Lipe')
    if 'cartolouco' in tokens:
        topic.append('Cartolouco')
    if 'fernandinho' in tokens:
        topic.append('Fernandinho')
    if 'selfie' in tokens:
        topic.append('Lucas Selfie')
    if 'carrieri' in tokens:
        topic.append('Carrieri')
    size = len(topic)

    if size == 1:
        return topic[0]
    return 'Geral'

# Create our listener
class MyStreamListener(tweepy.StreamListener):

    # Function on_status contains the logic for each streamed tweet
    def on_status(self, status):
        try:
            # Skip kpopers spaming tweets
            tweet = status.text
            if not ('trick' in tweet or 'kpop' in tweet):
                id = status.id_str
                time = status.created_at

                # Remove urls
                tweet = re.sub(r"http\S+|www\S+|https\S+", '', tweet.lower())

                # Remove punctuations (fastest way)
                tweet = tweet.translate(str.maketrans('', '', string.punctuation))

                # Classify the tweet
                freq = vectorizer_sav.transform([tweet])
                sentiment = classifier_sav.predict(freq)[0]

                # Get topic
                topic = get_topic(tweet)

                # print
                # print(id, tweet, time, sentiment, topic)

                # Insert in the database
                c.execute(insert_query,(id, time, tweet, sentiment, topic))
                conn.commit()

                # Delete the oldests tweets once it reachs the limit
                c.execute(delete_query)
                conn.commit()
                
                print("-----------------SAVED---------------------------")
                df = pd.read_sql("select count(*) from {}".format(settings.TABLE_NAME), conn)
                print(df)

        except Exception as e: 
            print(e)
            return True
    
    def on_error(self, status_code):
        if status_code == 420:
            return False

# Authenticate to Twitter API 
auth  = tweepy.OAuthHandler(keys.API_KEY, keys.API_SECRET_KEY)
auth.set_access_token(keys.ACCESS_TOKEN, keys.ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

# Stream portuguese tweets about the brazilian reality show "A Fazenda"
myStreamListener = MyStreamListener()
myStream = tweepy.Stream(auth = api.auth, listener=myStreamListener)
myStream.filter(track=['#AFazenda12'])