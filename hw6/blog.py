from BaseHandler import *
from google.appengine.api import memcache
from google.appengine.ext import db
import json
import time


class BlogEntry(db.Model):
    title = db.StringProperty(required=True)
    text = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)


def get_posts(update=False):
    if update or not memcache.get('posts'):
        posts = db.GqlQuery("SELECT * FROM BlogEntry ORDER BY created DESC LIMIT 10")
        memcache.set('posts', posts)
        memcache.set('cache-time', str(time.time()))
        dic = dict()
        dic['posts'] = posts
        dic['cacheDelay'] = int(time.time() - float(memcache.get('cache-time')))
        return dic

    else:
        dic = dict()
        dic['posts'] = memcache.get('posts')
        dic['cacheDelay'] = int(time.time() - float(memcache.get('cache-time')))
        return dic


def get_post(post_id, update=False):
    if update or not memcache.get(post_id):
        post = BlogEntry.get_by_id(int(post_id))
        if post:
            memcache.set(str(post_id), post)
            memcache.set('cacheDelay' + str(post_id), time.time())
            dic = dict()
            dic['title'] = post.title
            dic['text'] = post.text
            dic['cacheDelay'] = int(time.time() - float(memcache.get('cacheDelay' + str(post_id))))
            return dic
        else:
            return None

    else:
        post = memcache.get(str(post_id))
        dic = dict()
        dic['title'] = post.title
        dic['text'] = post.text
        dic['cacheDelay'] = int(time.time() - float(memcache.get('cacheDelay' + str(post_id))))
        return dic


class BlogFrontView(BaseHandler):
    def get(self):
        self.render("front_page.html", **get_posts())


class BlogFrontViewJSON(BaseHandler):
    def get(self):
        #First we set the right content-type header
        self.response.headers.add_header('Content-type', 'application/json_charset=UTF-8')

        posts = db.GqlQuery("SELECT * FROM BlogEntry ORDER BY created DESC LIMIT 10")
        json_content = []

        for post in posts.fetch(10):
            dic = {'content': post.text, 'subject': post.title}
            json_content.append(dic)

        self.response.out.write(json.dumps(json_content))


class BlogNewEntry(BaseHandler):
    def get(self):
        self.render("new_entry.html")

    def post(self):
        title = self.request.get('subject')
        content = self.request.get('content')

        if title and content:
            post = BlogEntry(title=title, text=content)
            post.put()
            get_posts(True)
            get_post(post.key().id(), True)
            self.redirect('/' + str(post.key().id()))
        else:
            error = "You have to give a title AND a text for a new post!"
            self.render("new_entry.html", title=title, text=content, errormessage=error)


class BlogPermalink(BaseHandler):
    def get(self, post_id):
        article = get_post(post_id)

        if article:
            self.render("post.html", **article)
        else:
            self.render("post.html", title="Not found", errormessage="Article not found... Sorry!")


class BlogPermalinkJSON(BaseHandler):
    def get(self, post_id):
        self.response.headers.add_header('Content-type', 'application/json_charset=UTF-8')

        article = BlogEntry.get_by_id(int(post_id))
        json_content = {'content': article.text, 'subject': article.title}

        if article:
            self.response.out.write(json.dumps(json_content))
        else:
            self.error(404)


class BlogCacheFlush(BaseHandler):
    def get(self):
        pass