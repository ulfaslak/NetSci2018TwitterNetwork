from twitter import Twitter, OAuth, TwitterHTTPError, TwitterStream
import twitter
import os
import urllib
import json
import datetime as dt
from dateutil import parser
from time import sleep
import re
import subprocess

# twitter tokens, keys, secrets, and Twitter handle in the following variables
CONSUMER_KEY = 'E19oBd9qdE1wXWiyixMfrubbI'
CONSUMER_SECRET ='IU5qiEwHJgKAVJN0fXMux79yIzsMISSjLORB3j8sXXvUFddlnV'
OAUTH_TOKEN = '2749655899-u4geaWEZHlCXtvk12wlVJ84JmSX4HIQuD3FEsDQ'
OAUTH_TOKEN_SECRET = 'NlUL020uY5mXW4nFonFI2PgWDMguv6V2aF9QGGQkCAly8'
TWITTER_HANDLE = "ulfaslak"
TWITTER_ID = 2749655899

def search_tweets(q, count=100, result_type="recent", lang='en'):
    return t.search.tweets(q=q, result_type=result_type, count=count, lang=lang)

def get_user_links_likes(user):
    return [
        (user, tweet['user']['screen_name'], str(parser.parse(tweet['created_at'])))
        for tweet in t.favorites.list(screen_name=user, count=100)
        if tweet['user']['screen_name'] in users
    ]

def update_users(new_users):
    with open('data/users', 'r') as fp:
        users = json.load(fp)
    with open('data/users', 'w') as fp:
        users = sorted(set(users) | set(new_users))
        json.dump(users, fp)
    return users
    
def update_links(new_links, filename):
    with open(filename, 'r') as fp:
        links = [tuple(l.split(",")) for l in fp.read().split("\n")[1:]]
    with open(filename, 'w') as fp:
        links = sorted(set(links) | set(new_links))
        fp.write("source,target,datetime\n")
        fp.write("\n".join([",".join(l) for l in links]))
        
t = Twitter(auth=OAuth(OAUTH_TOKEN, OAUTH_TOKEN_SECRET, CONSUMER_KEY, CONSUMER_SECRET))

# Get users that tweeted with #netsci2018 hashtag
print "Searching for tweets with hashtag '#NetSci2018'"
collection_tweets = search_tweets("#netsci2018")['statuses']
print "Loaded %d tweets"  % len(collection_tweets),

print "from",
users = sorted(set(update_users([tweet['user']['screen_name'] for tweet in collection_tweets])))  # Everybody who has tweeted
print "%d different users:" %len(users)

print "\n".join(users)
print "\n... saving users"

# For each, produce links from their favorites
print "\nGetting like-links for each user:"
links_likes = []
for user in users:
    try:
        links_user = get_user_links_likes(user)
    except twitter.TwitterHTTPError:
        print "Warning: Rate limit exceeded (user: %s), waiting 15 minutes" % user
        sleep(60 * 15)
        links_user = get_user_links_likes(user)
        continue
        
    print user, len(links_user)
    links_likes.extend(links_user)

print "\nTotal:", len(links)

# Produce retweet links
links_retweets = []
for tweet in collection_tweets:
    if 'retweeted_status' in tweet and tweet['retweeted_status']['user']['screen_name'] in users:
        links_retweets.append(
            (tweet['user']['screen_name'], tweet['retweeted_status']['user']['screen_name'], str(parser.parse(tweet['created_at'])))
        )
        
# Produce tag links
links_tags = []
for tweet in collection_tweets:
    if 'retweeted_status' not in tweet:
        for tagged_user in re.findall(r"(?<=^|(?<=[^a-zA-Z0-9-_\.]))@([A-Za-z]+[A-Za-z0-9_]+)", tweet['text']):
            if tagged_user:
                links_tags.append(
                    (tweet['user']['screen_name'], tagged_user, str(parser.parse(tweet['created_at'])))
                )
                    


print "\n... saving links"
update_links(links_likes, "data/links_likes.csv")
update_links(links_retweets, "data/links_retweets.csv")
update_links(links_tags, "data/links_tags.csv")

# Move stuff around
subprocess.call("cp data/links_likes.csv live_data/links_likes.csv".split())
subprocess.call("cd live_data && git add . && git commit -m "." && git push origin master")