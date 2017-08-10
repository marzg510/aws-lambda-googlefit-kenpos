#!/usr/bin/env python
# -*- coding: utf-8 -*-

from oauth2client import client
import httplib2
from apiclient.discovery import build
from oauth2client.file import Storage
from datetime import date, time, datetime, timedelta
import json,mechanize,re

TEST_DATA = [
  {
    'date': '2016-03-25', 
    'count': 1708
  }, 
  {
    'date': '2016-03-26', 
    'count': 1477
  }, 
  {
    'date': '2016-03-27', 
    'count': 1643
  }, 
  {
    'date': '2016-03-28', 
    'count': 8145
  }
]

def lambda_handler(event, context):
    # ConfigFile読み込み
    f = open('config.json', 'r')
    conf = json.load(f)
    f.close()
    # GoogleFitから歩数データ取得
    print 'get GoogleFit data'
    steps = getSteps(conf)
    # Kenposに登録
    print 'open KENPOS and set data'
    postKenops(steps, conf)
    print 'done'

def getSteps(conf):
    # 認証情報の読み込み
    import os
    from os import path
    from shutil import copyfile
    if not path.isfile('/tmp/googlefit_credential') :
        copyfile('./googlefit_credential' , '/tmp/googlefit_credential' )
        os.chmod('/tmp/googlefit_credential',0666)
    #
    storage = Storage('/tmp/googlefit_credential')
    credentials = storage.get()
    #
    http_auth = credentials.authorize(httplib2.Http())
    req = build('fitness', 'v1', http=http_auth)
    # 
    # 日別の2週間分の歩数取得(JST 4:00)
    stopDate = datetime.combine(date.today(), time(19)) - timedelta(days=1)
    startDate = stopDate - timedelta(days=13)
    #
    import time as t
    stopMillis=int(t.mktime(stopDate.timetuple()))*1000 
    startMillis=int(t.mktime(startDate.timetuple()))*1000
    #
    body = {
      "aggregateBy": [
        {
          "dataSourceId": "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps"
        }
      ],
      "startTimeMillis": startMillis,
      "endTimeMillis": stopMillis,
      "bucketByTime": {
        "durationMillis": "86400000"
      }
    }
    # 
    steps = req.users().dataset().aggregate(userId='me',body=body).execute()
    # 歩数データの整形
    dailySteps = []
    for data in steps['bucket']:
        startTime = datetime.fromtimestamp(int(data['startTimeMillis'])/1000) + timedelta(days=1)
        dataset = data['dataset'][0]
        if 'point' in dataset:
            value = dataset['point'][0]['value']
            dailySteps.append({
                'date' : startTime.strftime('%Y-%m-%d'),
                'count' : value[0]['intVal']
            })
    return dailySteps

def postKenops(steps,conf):
    loginId  = conf['login_id']
    password = conf['password']
    print "logining by " + loginId
    #
    br = mechanize.Browser()
    br.set_handle_robots(False)
    html = br.open('https://www.kenpos.jp/member/login')
    # ログイン
    br.select_form(nr=0)
    br['authKenpos2012[login_id]'] = loginId
    br['authKenpos2012[password]'] = password
    res = br.submit()
#    print res.read()
    # 歩数入力画面
    for link in br.links():
#        print link.text, link.url
        if u'記録をつける' in link.text:
            l = link
#    br.follow_link(text_regex = re.compile(u'記録をつける'.encode('utf-8')))
#    br.follow_link(text_regex = re.compile("記録をつける"))
    br.follow_link(l)
#    r = br.find_link(text_regex = re.compile("記録をつける"))
#    r = br.find_link(text="記録をつける")
#    print r
    br.select_form(nr=0)
    # 歩数入力
    print "updating step count"
#    for form in br.forms():
#        print form
#    print mechanize._form
    for step in steps:
        field = 'health[step_count_%s][value]' % (step['date'])
        try:
            br[field]=str(step['count'])
        except mechanize._form_controls.ControlNotFoundError :
            print 'skipping field:%s' % (field) 
    res = br.submit()
    #
    # 行動入力
    print "updating behavior"
    for link in br.links():
#        print link.text, link.url
        if u'行動項目入力' in link.text:
            l = link
#    br.follow_link(text_regex = u'行動項目入力'.encode('utf-8'))
    br.follow_link(l)
    for step in steps :
        url = '/healthAction/statusInput?date=%s' % (step['date'])
        try:
            br.open(url)
            headers = {
                'Content-Type' : 'application/x-www-form-urlencoded',
                'X-Requested-With' : 'XMLHttpRequest'
            }
            # ボタンを押す
        except mechanize.HTTPError :
            print 'skipping url:%s' % (url)
            continue

        for f in br.forms():
#            print f
            action_id = f.find_control(name='kenpos_member_health_action_status[health_action_id]').value
#            req_words  = "kenpos_member_health_action_status%5Bid%5D=" + f.find_control( name='kenpos_member_health_action_status[id]').value
            req_words = "&kenpos_member_health_action_status%5Bhealth_action_id%5D=" + action_id
            req_words += "&kenpos_member_health_action_status%5Btarget_date%5D=" + f.find_control(name='kenpos_member_health_action_status[target_date]').value
            req_words += "&kenpos_member_health_action_status%5B_csrf_token%5D=" + f.find_control(name='kenpos_member_health_action_status[_csrf_token]').value
            #
            actionFlg = 0
            if 'defalut' in conf['action'] :
                if conf['action']['defalut'] : actionFlg = 1
            if action_id in conf['action'] :
                if conf['action'][action_id] : actionFlg = 1
            url = 'https://www.kenpos.jp/healthAction/statusUpdate/%d?mode=gadget' % (actionFlg)
            #Post
            req = mechanize.Request(url, req_words, headers)
            res = br.open(req)
        #
    #

if __name__ == '__main__':
    lambda_handler( {}, {} )

