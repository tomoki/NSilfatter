#!/usr/bin/env python
#coding:utf-8

import user
import status

class favorite(dict):
    def __init__(self,js):
        self.update(js)
        self["source"] = user.TwitterUser(self.get("source"))
        self["target"] = user.TwitterUser(self.get("target"))
        self["target_object"] = status.TwitterStatus(self.get("target_object"))

    @property
    def source(self):
        return self.get("source")

    @property
    def target(self):
        return self.get("target")

    @property
    def target_object(self):
        return self.get("target_object")

    @property
    def event(self):
        return self.get("event")

class unfavorite(dict):
    def __init__(self,js):
        self.update(js)
        self["source"] = user.TwitterUser(self.get("source"))
        self["target"] = user.TwitterUser(self.get("target"))
        self["target_object"] = status.TwitterStatus(self.get("target_object"))

    @property
    def source(self):
        return self.get("source")

    @property
    def target(self):
        return self.get("target")

    @property
    def target_object(self):
        return self.get("target_object")

    @property
    def event(self):
        return self.get("event")
class friends(dict):
    def __init__(self,js):
        self.update(js)
    @property
    def friends(self):
        self.get("friends")
