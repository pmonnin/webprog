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
import webapp2
import re

form = """
<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8" />
        <title>ROT13</title>
    </head>
    <body>
        <h1>Sign up!</h1>
        <form method="post" action="/">
            <label for="username">Username</label>
            <input type="text" name="username" id="username" value="%(username)s" />
            <span style="color: red;">%(username_error)s</span>
            <br />
            <label for="password">Password</label>
            <input type="password" name="password" id="password" />
            <span style="color: red;">%(password_error)s</span>
            <br />
            <label for="verify">Re-type your password</label>
            <input type="password" name="verify" id="verify" />
            <span style="color: red;">%(verify_error)s</span>
            <br />
            <label for="email">Email (optionnal)</label>
            <input type="text" name="email" id="email" value="%(email)s" />
            <span style="color: red;">%(email_error)s</span>
            <br />
            <br />
            <input type="submit" />
       </form>
    </body>
</html>
"""


welcome_message = """
<!DOCTYPE html>
<html>
    <body>
        <h1>Welcome %(username)s!</h1>
    </body>
</html>
"""


user_re = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
password_re = re.compile("^.{3,20}$")
mail_re = re.compile("^[\S]+@[\S]+\.[\S]+$")


def verify_username(un):
    return user_re.match(un)


def verify_password(up):
    return password_re.match(up)


def verify_verify(up, uv):
    if up == uv:
        return True
    else:
        return False


def verify_email(email):
    return mail_re.match(email)


class MainHandler(webapp2.RequestHandler):
    def write_form(self, username="", email="", username_error="", password_error="", verify_error="", email_error=""):
        self.response.out.write(form % {"username": username, "username_error": username_error, "password_error": password_error, "verify_error": verify_error, "email": email, "email_error": email_error})

    def get(self):
        self.write_form()

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')

        if not verify_username(username):
            self.write_form(username, email, "Your username is invalid!")

        elif not verify_password(password):
            self.write_form(username, email, password_error="Invalid password")

        elif not verify_verify(password, verify):
            self.write_form(username, email, verify_error="Passwords don't match...")

        elif email and not verify_email(email):
            self.write_form(username, email, email_error="Invalid email")

        else:
            self.redirect("/welcome?username=" + username)


class WelcomeHandler(webapp2.RequestHandler):
    def get(self):
        self.response.out.write(welcome_message % {"username": self.request.get('username')})

app = webapp2.WSGIApplication([('/', MainHandler), ("/welcome", WelcomeHandler)], debug=True)