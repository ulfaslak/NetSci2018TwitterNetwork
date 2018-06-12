from twitter import Twitter, OAuth, TwitterHTTPError, TwitterStream
import twitter
import os
import urllib
import json
import datetime as dt
from dateutil import parser
from time import sleep

# twitter tokens, keys, secrets, and Twitter handle in the following variables
CONSUMER_KEY = 'E19oBd9qdE1wXWiyixMfrubbI'
CONSUMER_SECRET ='IU5qiEwHJgKAVJN0fXMux79yIzsMISSjLORB3j8sXXvUFddlnV'
OAUTH_TOKEN = '2749655899-u4geaWEZHlCXtvk12wlVJ84JmSX4HIQuD3FEsDQ'
OAUTH_TOKEN_SECRET = 'NlUL020uY5mXW4nFonFI2PgWDMguv6V2aF9QGGQkCAly8'
TWITTER_HANDLE = "ulfaslak"
TWITTER_ID = 2749655899

def search_tweets(q, count=1000, result_type="recent", lang='en'):
    return t.search.tweets(q=q, result_type=result_type, count=count, lang=lang)

def get_user_links(user):
    return [
        (user, tweet['user']['screen_name'], str(parser.parse(tweet['created_at'])))
        for tweet in t.favorites.list(screen_name=user, count=50)
        if tweet['user']['screen_name'] in users
    ]

def update_users(new_users):
    with open('users', 'r') as fp:
        users = json.load(fp)
    with open('users', 'w') as fp:
        users = sorted(set(users) | set(new_users))
        json.dump(users, fp)
    return users
    
def update_links(new_links):
    with open("links.csv", 'r') as fp:
        links = [tuple(l.split(",")) for l in fp.read().split("\n")[1:]]
        print links
    with open("links.csv", 'w') as fp:
        links = sorted(set(links) | set(new_links))
        fp.write("source,target,datetime\n")
        fp.write("\n".join([",".join(l) for l in links]))
        
t = Twitter(auth=OAuth(OAUTH_TOKEN, OAUTH_TOKEN_SECRET, CONSUMER_KEY, CONSUMER_SECRET))

# Get users that tweeted with #netsci2018 hashtag
print "Searching for users that tweeted with hashtag #NetSci2018:"
users = list(set(update_users([
    tweet['user']['screen_name']
    for tweet in search_tweets("#netsci2018")['statuses']
])))

print "\n".join(users)
print "\n... saving users (%d total)" % len(users)

# For each, produce links from their favorites
print "\nGetting out-links for each user:"
links = []
for user in users:
    try:
        links_user = get_user_links(user)
    except twitter.TwitterHTTPError:
        print "Warning: Rate limit exceeded (user: %s), waiting 15 minutes" % user
        sleep(300 * 15)
        links_user = get_user_links(user)
        continue
        
    print user, len(links_user)
    links.extend(links_user)

print "\nTotal:", len(links)

print "\n... saving links"
update_links(links)