#!/usr/bin/env python
#coding:utf-8

import threading
import urllib2
import twoauth
import time


class RestThread(threading.Thread):
    def __init__(self,client,args=(),kwargs={}):
        threading.Thread.__init__(self)
        self.client = client
        self.setDaemon(True)
        self.setName("Rests")
        self.timelines = []
        self.die = False
        self.api = self.client.api

    def add(self,timeline):
        self.timelines.append(timeline)

    def run(self):
        home_last_id = None
        mention_last_id = None
        con = True

        home = self.api.home_timeline(count=200)
        mentions = self.api.mentions(count=20)
        me = self.api.user_timeline(self.client.my_name,count=200)


        for s in home:
            self.client.statuses[s.id] = s

        for s in mentions:
            self.client.statuses[s.id] = s

        for s in me:
            self.client.statuses[s.id] = s

        h_ids = list(reversed([h.id for h in home]))
        m_ids = list(reversed([m.id for m in mentions]))

        for timeline in self.timelines:
            if timeline.mode == "home":
                timeline.prepend_new_statuses(h_ids,first=True)
            elif timeline.mode == "mention":
                timeline.prepend_new_statuses(m_ids,first=True)

        last_home_ids = h_ids[len(h_ids)-1]
        last_mentions_ids = m_ids[len(m_ids)-1]

        while con:
            try:
                home = self.api.home_timeline(since_id=last_home_ids,count=20)
                mentions = self.api.mentions(since_id=last_mentions_ids,count=20)
                h_ids = list(reversed([h.id for h in home]))
                m_ids = list(reversed([m.id for m in mentions]))

                for s in home:
                    self.client.statuses[s.id] = s

                for s in mentions:
                    self.client.statuses[s.id] = s

                for timeline in self.timelines:
                    if timeline.mode == "home":
                        timeline.prepend_new_statuses(h_ids)
                    elif timeline.mode == "mentions":
                        timeline.prepend_new_statuses(m_ids)

                last_home_ids = h_ids[len(h_ids)-1]
                last_mentions_ids = m_ids[len(m_ids)-1]
                time.sleep(60)

            except:
                time.sleep(60)


class StreamingThread(threading.Thread):
    def __init__(self,client,args=(),kwargs={}):
        threading.Thread.__init__(self)
        self.client = client
        self.setDaemon(True)
        self.setName("Streaming")

        self.args = args
        self.kwargs = kwargs

        self.timelines = []
        self.die = False
        self.s = twoauth.streaming.StreamingAPI(self.client.api.oauth)

    def add(self,timeline):
        self.timelines.append(timeline)

    def run(self):
        stream = self.s.user()
        stream.start()
        while not self.die:
            self.add_events(stream.pop())
            stream.event.wait()
        stream.stop()

    def destroy(self):
        self.die = True

    def add_events(self,events):
        new_statuses = set()
        es = []
        for event in events:
            # If event is new Status receive
            if isinstance(event,twoauth.status.TwitterStatus):
                new_statuses.add(event.id)
                if not event.id in self.client.statuses:
                    self.client.statuses[event.id] = event
                if not event.retweeted_status == None:
                    self.client.statuses[event.retweeted_status.id] = event.retweeted_status

            elif isinstance(event,twoauth.event.favorite):
                es.append(event)

            elif isinstance(event,twoauth.event.unfavorite):
                es.append(event)

            elif isinstance(event,twoauth.event.friends):
                pass

        if not len(new_statuses) == 0:
            for time in self.timelines:
                time.prepend_new_statuses(list(new_statuses))
