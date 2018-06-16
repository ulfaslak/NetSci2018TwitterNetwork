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
CONSUMER_KEY = ''
CONSUMER_SECRET =''
OAUTH_TOKEN = ''
OAUTH_TOKEN_SECRET = ''
TWITTER_HANDLE = "ulfaslak"

hashtags = ['#netsci2018', '#netsci18']

def search_tweets(q, count=100, result_type="recent", lang='en'):
    return t.search.tweets(q=q, result_type=result_type, count=count, lang=lang)

def tweet_in_subject(text):
    for hashtag in hashtags:
        if hashtag in text.lower():
            return True
    return False

def get_user_links_likes(user):
    try:
        return [
            (user, tweet['user']['screen_name'], str(parser.parse(tweet['created_at'])))
            for tweet in t.favorites.list(screen_name=user, count=100)
            if tweet['user']['screen_name'] in users and tweet_in_subject(tweet['text'])
        ]
    except KeyError: # Using keyError as dummy, insert correct error type
        print "Warning: API fails for user %s" % user
        return []

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
        
while True:
    t = Twitter(auth=OAuth(OAUTH_TOKEN, OAUTH_TOKEN_SECRET, CONSUMER_KEY, CONSUMER_SECRET))

    # Get users that tweeted with #netsci2018 hashtag
    print "Searching for tweets with hashtags '#NetSci2018' and '#NetSci18'"
    collection_tweets = []
    for hashtag in hashtags:
        collection_tweets += search_tweets(hashtag)['statuses']
    print "Loaded %d tweets"  % len(collection_tweets),

    print "from",
    users = sorted(set(update_users([
        tweet['user']['screen_name']
        for tweet in collection_tweets
        if tweet['text'][:2] != "RT"
    ])))  # Everybody who has tweeted
    print "%d different users:" %len(users)

    print "\n".join(users)
    print "\n... saving users"

    # Produce retweet links
    links_retweets = []
    for tweet in collection_tweets:
        if 'retweeted_status' in tweet and tweet['retweeted_status']['user']['screen_name'] in users:
            links_retweets.append(
                (tweet['user']['screen_name'], tweet['retweeted_status']['user']['screen_name'], str(parser.parse(tweet['created_at'])))
            )

    # Produce mention links
    links_mentions = []
    for tweet in collection_tweets:
        if 'retweeted_status' not in tweet:
            for mentioned_user in re.findall(r"(?<=^|(?<=[^a-zA-Z0-9-_\.]))@([A-Za-z]+[A-Za-z0-9_]+)", tweet['text']):
                if mentioned_user:
                    links_mentions.append(
                        (tweet['user']['screen_name'], mentioned_user, str(parser.parse(tweet['created_at'])))
                    )

    update_links(links_retweets, "data/links_retweets.csv")
    update_links(links_mentions, "data/links_mentions.csv")
    subprocess.call("bash sync.sh".split())

    # For each, produce links from their favorites
    print "\nGetting like-links for each user:"
    links_likes = []
    for user in users:
        try:
            links_user = get_user_links_likes(user)
        except twitter.TwitterHTTPError:
            print "Warning: Rate limit exceeded (user: %s), saving data and waiting 15 minutes" % user
            update_links(links_likes, "data/links_likes.csv")
            links_likes = []
            subprocess.call("bash sync.sh".split())
            sleep(60 * 15)
            try:
                links_user = get_user_links_likes(user)
            except:
                continue
            continue
        
        print user, len(links_user)
        links_likes.extend(links_user)

    print "\nTotal:", len(links_likes)

    
    print "\n... saving links"
    update_links(links_likes, "data/links_likes.csv")
    subprocess.call("bash sync.sh".split())
    
    print "Successfully updated data!"
