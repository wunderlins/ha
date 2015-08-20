#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Start application server on port 8080

The first command line argument will set the port to be bound. Remeber, you 
need root privvileges to bind ports below 1024.

"""

meta = {
	"name": "framework",
	"version": "0.0.1"
}

# setup paths
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'etc'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib', 'web'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib', 'wsgilog'))

# import modules
import web, config, json
import datetime
import time
import tempfile
import sys, logging
from wsgilog import WsgiLog
from cgi import escape
import usbauth
import hashlib
import sqlite3
import webctx

## global variables ############################################################

# url to class mapping
urls = (
  '/', 'webctx.index',
  '/env', 'webctx.env',
  '/json1', 'webctx.json1',
  '/json2', 'webctx.json2',
  '/image', 'webctx.image',
  '/login', 'webctx.login'
)

# default session values
session_default = {
	"uid": -1,
	"user": None,
	"email": None
}

## webpy extensions ############################################################

class service(web.application):
	""" allow to pass a custom port/ip into the application """
	def run(self, port=8080, ip='0.0.0.0', *middleware):
		func = self.wsgifunc(*middleware)
		return web.httpserver.runsimple(func, (ip, port))

class Log(WsgiLog):
	""" extend logger, logging to file in var/ """
	def __init__(self, application):
		WsgiLog.__init__(
			self,
			application,
			logformat = '%(message)s',
			tofile = True,
			toprint = True,
			file = config.app_logfile,
			#when = "D",
			#interval = 1,
			#backups = "1000"
		)

class hooks(object):
	@staticmethod
	def load():
		web.debug("Loadhook")
		#web.debug(webctx.session.uid)
		#return "BEGIN"
	
	@staticmethod
	def unload():
		web.debug("Unloadhook")
		#return "ENDE"


# redirect webserver logs to file
#weblog = open(config.web_logfile, "ab")
#sys.stderr = weblog
#sys.stdout = weblog

def init_session(app):
	#global app
	web.debug(web.config.get('_session'))
	if web.config.get('_session') is None:
		web.debug("Setting up new session ...")
		web.config.session_parameters['cookie_name'] = meta["name"] + "_"
		web.config.session_parameters['timeout'] = config.session_timeout,
		web.config.session_parameters['secret_key'] = config.session_salt
		web.config.session_parameters['cookie_domain'] = config.session_cookie_domain
		web.config.session_parameters['ignore_expiry'] = config.session_ignore_expiry
		web.config.session_parameters['ignore_change_ip'] = config.session_ignore_change_ip
		web.config.session_parameters['expired_message'] = config.session_expired_message

		temp = tempfile.mkdtemp(dir=config.session_dir, prefix='session_')
		webctx.session = web.session.Session(
			app, 
			web.session.DiskStore(temp), 
			initializer = session_default
		)
		#for k in session_default.keys():
		#	webctx.session[k] = session_default[k]
		#webctx.session.uid = -1
		#web.debug(webctx.session.keys())
	else:
		web.debug("Reusing session ...")
		webctx.session = web.config._session
		"""
		try:
			webctx.session["uid"]
		except:
			webctx.session = session_default
		"""
	
	#web.debug("session.uid: %s" % webctx.session.uid) 
	#return webctx.session

## main function ###############################################################

"""
try:
	webctx.session
except NameError:
	web.debug("Resetting session ...")
	webctx.session = None
"""

app = None
if __name__ == "__main__":
	web.config.debug = False

	app = service(urls, globals())
	# session setup, make sure to call it only once if in debug mode
	init_session(app)
	
	app.add_processor(web.loadhook(hooks.load))
	app.add_processor(web.unloadhook(hooks.unload))

	#webctx.session["pid"] += 1
	#print "starting ..."
	#app.add_processor(web.loadhook(loadhook))
	#app.add_processor(web.unloadhook(unloadhook))
	#app.run(config.port, "0.0.0.0")
	
	#webctx.session = get_session(app)

	app.run(config.port, "0.0.0.0", Log)


