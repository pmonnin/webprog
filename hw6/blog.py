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
        memcache.set('cache-time', time.time())
        dic = dict()
        dic['posts'] = posts
        dic['cacheDelay'] = int(float(time.time()) - float(memcache.get('cache-time')))
        return dic

    else:
        dic = dict()
        dic['posts'] = memcache.get('posts')
        dic['cacheDelay'] = int(float(time.time()) - float(memcache.get('cache-time')))
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
            self.redirect('/' + str(post.key().id()))
        else:
            error = "You have to give a title AND a text for a new post!"
            self.render("new_entry.html", title=title, text=content, errormessage=error)


class BlogPermalink(BaseHandler):
    def get(self, post_id):
        article = BlogEntry.get_by_id(int(post_id))

        if article:
            self.render("post.html", title=article.title, text=article.text)
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