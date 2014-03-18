#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import webapp2
from google.appengine.ext import db
import jinja2

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)


class BlogEntry(db.Model):
    title = db.StringProperty(required=True)
    text = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)


class BaseHandler(webapp2.RequestHandler):
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)


class BlogFrontView(BaseHandler):
    def get(self):
        posts = db.GqlQuery("SELECT * FROM BlogEntry ORDER BY created DESC LIMIT 10")

        self.render("front_page.html", posts=posts)


class BlogNewEntry(BaseHandler):
    def get(self):
        self.render("new_entry.html")

    def post(self):
        title = self.request.get('subject')
        content = self.request.get('content')

        if title and content:
            post = BlogEntry(title=title, text=content)
            post.put()

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


app = webapp2.WSGIApplication([('/', BlogFrontView), ('/newpost', BlogNewEntry), (r'/(\d+)', BlogPermalink)], debug=True)
