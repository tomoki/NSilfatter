#!/usr/bin/env python
#coding:utf-8

import re
import datetime

class TwitterTool(object):
    _urlpattern = ur"(?P<url>https?://[^\s　]*)"
    _userpattern = ur"(?P<user>@\w+)"

    def __init__(self):
        self.reurl = re.compile(self._urlpattern)
        self.reuser = re.compile(self._userpattern)

    def get_colored_url(self,string):
        return self.reurl.sub(
                '<span foreground="#0000FF" underline="single">\g<url></span>',
                string)

    def get_colored_user(self,string):
        return self.reuser.sub(
                '<span foreground="#0000FF">\g<user></span>',
                string)

    def get_urls(self,string):
        url_iter = self.reurl.finditer(string)
        urls = []
        for i in url_iter:
            urls.append(i.group("url"))

        return tuple(urls)

    def get_users(self, string):
        user_iter = self.reuser.finditer(string)
        users = []
        for i in user_iter:
            users.append(i.group('user'))

        return users
