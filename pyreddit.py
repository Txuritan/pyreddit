from blitzdb import Document, FileBackend
from multiprocessing.dummy import Pool as ThreadPool
from sys import platform
from bs4 import BeautifulSoup
import os
import subprocess
import re
import wget
import requests
import time
import json
import logging


class Post(Document):
    pass


class PyReddit:
    def __init__(self, sub_json):

        if sub_json is not None:
            self.notifications = bool(sub_json["notifications"])
        else:
            self.notifications = False

        if sub_json is not None:
            self.once = bool(sub_json["once"])
        else:
            self.once = False

        if sub_json is not None:
            self.sub_json = sub_json
        else:
            quit(-1)

        self.log_prefix = "[" + sub_json["sub"] + "]: "

        logging.info(self.log_prefix + "Sub Reddit: " + sub_json["sub"])

        if not os.path.exists(sub_json["sub"]):
            os.makedirs(sub_json["sub"])

        self.database = FileBackend(sub_json["sub"] + "/database")

        fake_post = Post({"postID": "fakePost"})
        self.database.save(fake_post)
        self.database.commit()

        self.last_post = ""
        self.__sub_reddit(None)

    def __bar_none(self, current, total, width=0):
        pass

    def __send_notification(self, post_data):

        title = post_data["data"]["title"]

        # Check platform
        if platform == "linux" or platform == "linux2":
            if subprocess.check_output("uname -o") == "Android":
                os.system("termux-notification -t \"PyReddit: Downloaded Image\" -c \"[" + self.sub_json["sub"] + "] " + title + "\"")
            else:
                print()
        elif platform == "darwin":
            print()
        elif platform == "win32":
            print()

    def __save_post(self, post_data):

        url = post_data["data"]["url"]

        try:
            self.database.get(Post, {"postID": post_data["data"]["id"]})

            logging.info(self.log_prefix + "Post already downloaded")

        except Post.DoesNotExist:
            logging.info(self.log_prefix + "Attempting to download post: " + post_data["data"]["id"])
            logging.info(self.log_prefix + "\t url: " + post_data["data"]["url"])

            # Check for direct URLs

            # https://regex101.com/r/dgRENQ/1/
            # Imgur Regex
            if re.match(r"((http|https)://)?[i]\.imgur\.com/([a-zA-Z0-9]{7})\.(png|jpg|gif)", url):
                logging.info(self.log_prefix + "Downloading post: " + post_data["data"]["id"])

                wget.download(url, self.sub_json["sub"] + "/" + re.sub(r"((http|https)://)?[i]\.imgur\.com/", "", url), self.__bar_none)

                post = Post({"postID": post_data["data"]["id"]})
                self.database.save(post)
                self.database.commit()

                if self.notifications:
                    self.__send_notification(post_data)

                logging.info(self.log_prefix + "Downloaded post: " + post_data["data"]["id"])

            # https://regex101.com/r/w9rot4/1/
            # Tumblr Regex
            elif re.match(r"((http|https)://)?([0-9]{2})\.media\.tumblr\.com/([a-z0-9]{32})/tumblr_([a-zA-Z0-9]{19})_((r1)_)?([0-9]{4})\.(png|jpg|gif)", url):
                logging.info(self.log_prefix + "Downloading post: " + post_data["data"]["id"])

                wget.download(url, self.sub_json["sub"] + "/" + re.sub(r"((http|https)://)?([0-9]{2})\.media\.tumblr\.com/([a-z0-9]{32})/", "", url), self.__bar_none)

                post = Post({"postID": post_data["data"]["id"]})
                self.database.save(post)
                self.database.commit()

                if self.notifications:
                    self.__send_notification(post_data)

                logging.info(self.log_prefix + "Downloaded post: " + post_data["data"]["id"])

            # https://regex101.com/r/39DS9S/10/
            # Deviantart Regex
            elif re.match(r"((http|https)://)?(pre|img|orig)([0-9][0-9])(\.deviantart\.net)/([^\s]{4})/([^\s]|[^\s]{2})/(pre/([fi])/)?([^\s]{4})/([^\s]{3})/([a-z0-9])/([a-z0-9])/.*(_by_).*(-[a-z0-9]{7})\.(png|jpg|gif)", url):
                logging.info(self.log_prefix + "Downloading post: " + post_data["data"]["id"])

                wget.download(url, self.sub_json["sub"] + "/" + re.sub(r"((http|https)://)?(pre|img|orig)([0-9][0-9])(\.deviantart\.net)/([^\s]{4})/([^\s]|[^\s]{2})/(pre/[fi]/)?([^\s]{4})/([^\s]{3})/([a-z0-9])/([a-z0-9])/", "", url), self.__bar_none)

                post = Post({"postID": post_data["data"]["id"]})
                self.database.save(post)
                self.database.commit()

                if self.notifications:
                    self.__send_notification(post_data)

                logging.info(self.log_prefix + "Downloaded post: " + post_data["data"]["id"])

            # Redd.it Regex
            elif re.match(r"((http|https)://)?i\.redd\.it/([a-z0-9]{12})\.(png|jpg|gif)", url):
                logging.info(self.log_prefix + "Downloading post: " + post_data["data"]["id"])

                wget.download(url, self.sub_json["sub"] + "/" + re.sub(r"((http|https)://)?[i]\.redd\.it/", "", url), self.__bar_none)

                post = Post({"postID": post_data["data"]["id"]})
                self.database.save(post)
                self.database.commit()

                if self.notifications:
                    self.__send_notification(post_data)

                logging.info(self.log_prefix + "Downloaded post: " + post_data["data"]["id"])

            # Check for indirect URLs

            # Imgur Image
            elif re.match(r"((http|https)://)?imgur\.com/([a-zA-Z0-9]{7})", url):
                logging.info(self.log_prefix + "Downloading post: " + post_data["data"]["id"])

                request = requests.get(url)
                content = request.content
                soup = BeautifulSoup(content, "html.parser")
                image_url = soup.find_all("a", class_="zoom")

                if image_url is not None and len(image_url) > 0:
                    if re.match(r"((http|https)://)?(//)?[i]\.imgur\.com/([a-zA-Z0-9]{7})\.(png|jpg|gif)", image_url[0]["href"]):
                        logging.info(self.log_prefix + "\tImgur URL: " + image_url[0]["href"])

                        wget.download("http:" + image_url[0]["href"], self.sub_json["sub"] + "/" + post_data["data"]["id"] + re.sub(r"((http|https)://)?(//)?[i]\.imgur\.com/([a-zA-Z0-9]{7})", "", image_url[0]["href"]), self.__bar_none)

                        post = Post({"postID": post_data["data"]["id"]})
                        self.database.save(post)
                        self.database.commit()

                        if self.notifications:
                            self.__send_notification(post_data)

                    logging.info(self.log_prefix + "Downloaded post: " + post_data["data"]["id"])
                else:
                    logging.info(image_url)
                    logging.error(self.log_prefix + "Downloading post failed: " + post_data["data"]["id"])

            # Imgur Album
            elif re.match(r"((http|https)://)?imgur\.com/a/([a-zA-Z0-9]{7})", url):
                logging.info(self.log_prefix + "Downloading album: " + post_data["data"]["id"])

                request = requests.get(url)
                content = request.content
                soup = BeautifulSoup(content, "html.parser")
                image_url = soup.find_all("a", class_="zoom")

                if image_url is not None and len(image_url) > 0:

                    logging.info(self.log_prefix + "\tImgur Album URL: " + post_data["data"]["url"])

                    for i in range(len(image_url)):
                        logging.info(self.log_prefix + "Downloading album image: " + post_data["data"]["id"] + str(i))

                        wget.download("http:" + image_url[i]["href"], self.sub_json["sub"] + "/" + post_data["data"]["id"] + "-" + str(i) + re.sub(r"((http|https)://)?(//)?[i]\.imgur\.com/a/([a-zA-Z0-9]{7})", "", image_url[i]["href"]), self.__bar_none)

                        if self.notifications:
                            self.__send_notification(post_data)

                        logging.info(self.log_prefix + "Downloaded album image: " + post_data["data"]["id"] + str(i))

                    post = Post({"postID": post_data["data"]["id"]})
                    self.database.save(post)
                    self.database.commit()

                    logging.info(self.log_prefix + "Downloaded album: " + post_data["data"]["id"])
                else:
                    logging.info(image_url)
                    logging.error(self.log_prefix + "Downloading album failed: " + post_data["data"]["id"])

            else:
                logging.error(self.log_prefix + "ERROR: No method for downloading")
                logging.error(self.log_prefix + "Please send the url: [" + url + "] to the developer to get it fixed")

    def __sub_reddit(self, last_post):

        if last_post is not self.last_post:
            global temp_last_post

            if last_post is None:
                try:
                    request = requests.get("https://www.reddit.com/r/" + self.sub_json["sub"].replace("/", "") + "/new/.json?limit=1000")

                    if request.status_code is not 200:
                        self.__sub_reddit(None)

                    # Contains the source from the Reddit JSON
                    sub_data = request.json()

                    for post in sub_data["data"]["children"]:
                        self.__save_post(post)
                        time.sleep(1)

                    temp_last_post = sub_data["data"]["children"][len(sub_data["data"]["children"])]["data"]["name"]

                except KeyError:
                    self.__sub_reddit(None)

            else:
                try:
                    request = requests.get("https://www.reddit.com/r/" + self.sub_json["sub"].replace("/", "") + "/new/.json?limit=1000&after=" + last_post)

                    if request.status_code is not 200:
                        self.__sub_reddit(None)

                    # Contains the source from the Reddit JSON
                    sub_data = request.json()

                    for post in sub_data["data"]["children"]:
                        self.__save_post(post)
                        time.sleep(1)

                    temp_last_post = sub_data["data"]["children"][len(sub_data["data"]["children"])]["data"]["name"]

                except KeyError:
                    self.__sub_reddit(last_post)

            self.last_post = temp_last_post

            while True:
                try:
                    self.__sub_reddit(temp_last_post)
                except KeyboardInterrupt:
                    break

        else:
            try:
                request = requests.get("https://www.reddit.com/r/" + self.sub_json["sub"].replace("/", "") + "/new/.json?limit=1000")

                if request.status_code is not 200:
                    self.__sub_reddit(None)

                # Contains the source from the Reddit JSON
                sub_data = request.json()

                for post in sub_data["data"]["children"]:
                    self.__save_post(post)
                    time.sleep(1)

            except KeyError:
                self.__sub_reddit(last_post)

            while True:
                try:
                    self.__sub_reddit(last_post)
                except KeyboardInterrupt:
                    break


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')

    with open('subs.json') as data_file:
        data = json.load(data_file)

    subs = data["subs"]

    # Get number of subs and set the amount ot threads to that
    pool = ThreadPool(len(subs))

    # Run sub_reddit that many times passing over the subs variable
    pool.map(PyReddit, subs)
