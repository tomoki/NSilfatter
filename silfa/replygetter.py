#!/usr/bin/env python
#coding:utf-8

import threading
import time
import timeline as tl
import gtk

class InReplyGetter(object):
    def __init__(self,client):
        self.status_store = client.statuses
        self.api = client.api
        self.semaphore = threading.BoundedSemaphore(1)
        self.timelines = []
        self.getting = []

    def get(self,status):
        if status.in_reply_to_status_id in self.status_store:
            return self.status_store[status.in_reply_to_status_id]
        else:
            if not status.in_reply_to_status_id in self.getting:
                self.new(status.in_reply_to_status_id)
                return None
            else:
                return None

    def new(self,id):
        newstatus = NewStatus(id,self.api,self.timelines,self.status_store,self.semaphore,self.getting)
        try:
            newstatus.start()
        except:
            pass

    def add_timeline(self,timeline):
        if not timeline in self.timelines:
            self.timelines.append(timeline)
    
class NewStatus(threading.Thread):
    def __init__(self,st_id,api,timelines,status_store,semaphore,getting):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.api = api
        self.setName("StatusGetting :%d"%st_id)
        self.st_id = st_id
        self.timelines = timelines
        self.status_store = status_store
        self.semaphore = semaphore
        self.getting = getting
        getting.append(self.st_id)

    def run(self):
        self.semaphore.acquire()
        for i in range(1):
            try:
                in_status = self.api.status_show(self.st_id)
                break
            except:
                self.semaphore.release()
                raise

        self.semaphore.release()
        self.status_store[self.st_id] = in_status
        time.sleep(1)

        for timeline in self.timelines:
            ite = timeline.liststore.get_iter_first()
            while ite:
                status = self.status_store[timeline.liststore.get_value(ite,tl.TWEET_ID)]
                if not status.in_reply_to_status_id == None:
                    if self.st_id == status.in_reply_to_status_id:
                        timeline.add_reply_to(in_status,ite)
                ite = timeline.liststore.iter_next(ite)
        self.getting.remove(self.st_id)
