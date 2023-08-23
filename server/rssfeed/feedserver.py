
import feedparser
from pymongo import MongoClient
from datetime import datetime, timedelta
import requests
import json
import time

import server.commons.utils as util
import server.commons.constants as consts


# db isinstance
client = MongoClient()
db = client[consts.DB_NAME]
table = db.rss_feeds

class FeedParser:
    '''Fetches rss feed url details'''
    def __init__(self, feed_url):
        self.feed_url = feed_url

    def get_feeds(self):
        feeds = []
        news_feed = feedparser.parse(self.feed_url[0])
        for entry in news_feed.entries:
            feed_details = { "publish": entry.published,
                           "title": entry.title,
                           "summary": entry.summary,
                            "date": datetime.now(),
                             "link": entry.link,
                             "agency_id": self.feed_url[1]}
            feeds.append(feed_details)
        return feeds

class ThirdPartyFeed:
    '''Create stories from rss feeds'''
    user_id = ""

    def __init__(self, feed_urls):
        self.feed_urls = feed_urls
        self.set_user_id()

    def get_user_id(self):
        try:
            demo_user = {"email": "journo_feed_server@journo.com", "password": "journo_feed_server"}
            req = requests.post(util.get_request_server_url("users-sessions"), data=json.dumps(demo_user))
            response = req.json()
            return response.get("_id")
        except:
            pass

    def set_user_id(self):
        try:
            user_id = self.get_user_id()
            if user_id == None:
                demo_user = {"display_name": "Journo Feed Server", "username": "journo_feed_server", "password": "journo_feed_server",
                             "email": "journo_feed_server@journo.com", "mobile": 9876543210,
                             "roles": []
                             }
                req = requests.post(util.get_request_server_url("users"), data=json.dumps(demo_user))
                response = req.json()
                if response.get("ok"):
                    self.user_id = self.get_user_id()
            else:
                self.user_id = user_id
        except:
            pass

    def create_stories(self):
        for feed_url in self.feed_urls:
            self.create_story_from(feed_url)

    def create_story_from(self, feed_url):
        parser = FeedParser(feed_url)
        feeds = parser.get_feeds()
        stories_to_create = []

        for feed in feeds:
            if not self.post_is_in_db(feed["title"], feed_url[1]):
                stories_to_create.append(feed)

        if len(stories_to_create) > 0:
            result = table.insert_many(stories_to_create)
            print(len(stories_to_create), " documents inserted.")
            print(stories_to_create)
            self.postStories(stories_to_create)
        else:
            print("No updated feed")

    def postStories(self, storiesFeed):
        """post stories API"""
        for feed in storiesFeed:
            date_time_obj = datetime.strptime(feed["publish"], '%a, %d %b %Y %H:%M:%S %Z')
            story = {
                "story_title": feed["title"],
                     "category_id": "",
                     "description": feed["summary"],
                      "tags": [], "new_tags": [], "attachments": [],
                     "incident_date": date_time_obj.strftime("%Y-%m-%d"),
                      "user_id": self.user_id,
                     "incident_time": date_time_obj.strftime("%H:%M:%S"),
                    "link": feed["link"],
                    "agency_id": feed["agency_id"]}
            req = requests.post(util.get_request_server_url("stories"), data=json.dumps(story))
            response = req.json()
            if not response.get("ok"):
                table.remove({'title': feed["title"], "agency_id": feed["agency_id"]})

    def post_is_in_db(self, title, agency_id):
        feed = table.find_one({'title': title, "agency_id": agency_id})
        return feed != None

    @classmethod
    def clean_week_old_feed(cls):
        """Delete week old feed to keep database small"""
        data_a_week_ago = (datetime.now() - timedelta(days=7))
        x = table.remove({"date": {"$lt": data_a_week_ago}})
        print(x['n'], " documents deleted.")


if __name__ == "__main__":
    try:
        rssFeedUrls = []
        req = requests.get(url=util.get_request_server_url("agencies"), params=[])
        data = req.json()
        for agency in data.get("agencies") or []:
            id = agency["_id"]
            url = (agency.get("config") or {}).get("url")
            if url:
                rssFeedUrls.append((url, id))

        timesOfIndiaFeed = ThirdPartyFeed(rssFeedUrls)
        last_cleanup = time.time()
        while True:
            curr_time = time.time()
            if (curr_time - last_cleanup) >= 10 * 60 * 60:  # 10 hour
                last_cleanup = curr_time
                ThirdPartyFeed.clean_week_old_feed()
            timesOfIndiaFeed.create_stories()
            time.sleep(2 * 60)
    except Exception as ex:
        print(" exception occured ", str(ex))
        pass


