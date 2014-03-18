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
import re
import cgi
import random
import string
import hashlib

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)


class Accounts(db.Model):
    username = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    email = db.StringProperty()


class BaseHandler(webapp2.RequestHandler):
    cookie_hash = "zfiizuyz[4"

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)


class SignUpHandler(BaseHandler):
    USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    PASS_RE = re.compile(r"^.{3,20}$")
    EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")

    def valid_username(self, username):
        return username and self.USER_RE.match(username)

    def exist_username(self, username):
        notExist = False

        if username:
            result = db.GqlQuery("SELECT * FROM Accounts WHERE username='" + username + "'")

            if result.count() != 0:
                notExist = False
            else:
                notExist = True

        return notExist

    def valid_password(self, password):
        return password and self.PASS_RE.match(password)

    def valid_verify(self, password, verify):
        return verify and verify == password

    def valid_email(self, email):
        return not email or self.EMAIL_RE.match(email)

    def get(self):
        self.render("signup-form.html")

    def post(self):
        username = cgi.escape(self.request.get('username'))
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')
        has_error = False
        params = dict(username=username, email=email)

        if not self.valid_username(username):
            params['error_username'] = "Invalid username"
            has_error = True

        if not self.exist_username(username):
            params['error_username'] = "User already exists. Sorry :("
            has_error = True

        if not self.valid_password(password):
            params['error_password'] = "Invalid password"
            has_error = True

        if not self.valid_verify(password, verify):
            params['error_verify'] = "Passwords don't match"
            has_error = True

        if not self.valid_email(email):
            params['error_email'] = "Invalid email"
            has_error = True

        if has_error:
            self.render('signup-form.html', **params)
        else:
            #First, hash the password
            salt = ''.join(random.choice(string.letters) for i in range(5))
            passhash = str(hashlib.sha256(password + salt).hexdigest()) + "|" + salt

            #Put the user in DB
            if email:
                user = Accounts(username=username, password=passhash, email=email)
            else:
                user = Accounts(username=username, password=passhash)
            user.put()

            #Cookie and redirect
            self.response.headers.add_header('Set-Cookie', "user_id=" + str(user.key().id()) + "|"
                                             + str(hashlib.sha256(self.cookie_hash + str(user.key().id())).hexdigest())
                                              + "; Path='/'")
            self.redirect('/welcome')


class WelcomeHandler(BaseHandler):
    def get(self):
        id = str(self.request.cookies.get('user_id'))

        if id and id != "":
            id = id.split('|')

            if id[1] == str(hashlib.sha256(self.cookie_hash + id[0]).hexdigest()):
                user = Accounts.get_by_id(int(id[0]))
                self.render('welcome.html', username=user.username)
            else:
                self.redirect('/signup')

        else:
            self.redirect('/signup')

class LoginHandler(BaseHandler):
    def get(self):
        self.render('login.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        has_error = False

        if not username or not password:
            has_error = True
        else:
            result = db.GqlQuery("SELECT * FROM Accounts WHERE username='" + username + "'")

            if result.count() != 0:
                user = result.get()

                salt = user.password.split('|')[1]

                if user.password.split('|')[0] != str(hashlib.sha256(password + salt).hexdigest()):
                    has_error = True
            else:
                has_error = True

        if has_error:
            self.render('login.html', error="Invalid login")
        else:
            self.response.headers.add_header('Set-Cookie', "user_id=" + str(user.key().id()) + "|"
                                             + str(hashlib.sha256(self.cookie_hash + str(user.key().id())).hexdigest())
                                             + "; Path='/'")
            self.redirect('/welcome')


class LogoutHandler(BaseHandler):
    def get(self):
        self.response.headers.add_header('Set-Cookie', "user_id=; Path='/'")
        self.redirect('/signup')


app = webapp2.WSGIApplication([
                              ('/signup', SignUpHandler),
                              ('/', SignUpHandler),
                              ('/welcome', WelcomeHandler),
                              ('/login', LoginHandler),
                              ('/logout', LogoutHandler)
                              ], debug=True)
