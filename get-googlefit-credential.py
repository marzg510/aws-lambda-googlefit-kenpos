#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

from oauth2client import client
import httplib2
from apiclient.discovery import build
from oauth2client.file import Storage
import webbrowser
import sys

## credentialの入手と保管
flow = client.flow_from_clientsecrets('client_secrets.json',
    scope=['https://www.googleapis.com/auth/fitness.activity.read',
           'https://www.googleapis.com/auth/fitness.body.read',
           'https://www.googleapis.com/auth/fitness.location.read'] ,
    redirect_uri='urn:ietf:wg:oauth:2.0:oob'
)
auth_uri = flow.step1_get_authorize_url()
#webbrowser.open(auth_uri)
print('Go to the following link in your browser:')
print('\n')
print(auth_uri)
print('verification code:' ,end='')
osecret=sys.stdin.readline()
credentials = flow.step2_exchange(osecret)
storage = Storage('googlefit_credential')
storage.put(credentials)
print('Saved Application Default Credentials.')
