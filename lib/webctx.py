#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
os.environ["NLS_LANG"] = "GERMAN_SWITZERLAND.UTF8"

import web, config, json
import datetime
import time
import re
import base64
import sys
import usbauth
import hashlib
import sqlite3
import cx_Oracle
import smtplib

tns_str = "(DESCRIPTION = "+\
	"(FAILOVER = ON)(LOAD_BALANCE = OFF)(ENABLE=BROKEN)(ADDRESS_LIST ="+\
		"(ADDRESS = (PROTOCOL = TCP)(HOST = oraisop.uhbs.ch)(PORT = 1545))"+\
		"(ADDRESS = (PROTOCOL = TCP)(HOST = oraisop2.uhbs.ch)(PORT = 1545)))"+\
	"(CONNECT_DATA =(SERVICE_NAME = ISOP_PRI.WORLD)"+\
	"(failover_mode=(type=select) (method=basic))))"


#session = None

def oraconn():
	con = cx_Oracle.connect('oppsc', 'oppsc', tns_str)
	cursor = con.cursor()
	
	return (con, cursor)


def is_dict(d):
	""" additional template function, registered with web.template.render """
	return type(d) is dict

class status(web.HTTPError):
	""" custom http error handler """
	http_codes = {	
		'100': 'Continue', '101': 'Switching Protocols',
		'200': 'OK', '201': 'Created', '202': 'Accepted',
				'203': 'Non-Authoritative Information','204': 'No Content',
				'205': 'Reset Content', '206': 'Partial Content', 
		'300': 'Multiple Choices', '301': 'Moved Permanently', '302': 'Found',
				'303': 'See Other', '304': 'Not Modified', '305': 'Use Proxy',
				'306': '(Unused)', '307': 'Temporary Redirect', 
		'400': 'Bad Request', '401': 'Unauthorized', '402': 'Payment Required',
				'403': 'Forbidden', '404': 'Not Found', '405': 'Method Not Allowed',
				'406': 'Not Acceptable', '407': 'Proxy Authentication Required',
				'408': 'Request Timeout', '409': 'Conflict', '410': 'Gone',
				'411': 'Length Required', '412': 'Precondition Failed',
				'413': 'Request Entity Too Large', '414': 'Request-URI Too Long',
				'415': 'Unsupported Media Type', '416': 'Requested Range Not Satisfiable',
				'417': 'Expectation Failed',
		'500': 'Internal Server Error', '501': 'Not Implemented',
				'502': 'Bad Gateway', '503': 'Service Unavailable', 
				'504': 'Gateway Timeout', '505': 'HTTP Version Not Supported'
	}
	
	def _http_code_lookup(self, code):
		out = None
		try:
			out = self.http_codes[str(code)]
			out = str(code) + " " + out
		except:
			out = "520 Unknown Error"
		
		return out
	
	code = None
	status = None
	headers = None
	
	def __init__(self, code, data=None, headers=None):
		self.code = code
		self.headers = {'Content-Type': 'text/html'}
		self.status = self._http_code_lookup(code)
		self.data = "<h1>" + str(self.status) + "</h1>"
		
		if headers != None:
			self.headers = headers
		if data != None:
			self.data = data
		
	def fail(self):
		web.debug(self.status)
		web.debug(self.headers)
		web.debug(self.data)
		web.HTTPError.__init__(self, self.status, self.headers, self.data)

## page methods ################################################################

class webctx(object):
	session = None
	no_auth = False
	__authenticated = False
	def auth_check(self):
		""" check if user is authenticated """
		
		"""
		try:
			session.uid
		except:
			web.debug("creating session")
			for e in session_default:
				session[e] = session_default[e]
		"""
		
		#session = get_session()
		
		# check if we have a valid session
		if session != None and session.uid > 0:
			self.__authenticated = True
			return True
		
		# authentication for this request not required
		if self.no_auth == True:
			return True
			
		# check if the user has submitted credentials
		return None
	
	def render(self):
		return web.template.render('template', globals={
			'is_dict': is_dict,
			'ctx': web.ctx,
			'config': config
		})
	
	def error(self, code):
		st = status(code)
		content = self.render().error(code, st.status, "sss")
		st.fail()

class login(webctx):
	no_auth = True
	
	def GET(self):
		#global session
	
		user_data = web.input(logout=False)
		web.debug(user_data.logout)
		if (user_data.logout == "true"):
			#session = session_default
			session.kill()
			raise web.seeother(config.baseurl + '/')
	
	""" authenticate user """
	def POST(self):
		
		# read posted json data
		data = web.data()
		credentials = json.loads(data)
		
		username = credentials["username"]
		password = credentials["password"]
		
		# check credentials against database
		pwhash = hashlib.md5(password).hexdigest()
		web.debug(pwhash)
		authdb = sqlite3.connect('etc/user.db')
		cur = authdb.cursor()
		sql = 'SELECT id FROM user WHERE username=? AND password=?'
		web.debug(sql)
		check = cur.execute(sql, (username, pwhash))
		web.debug(str(check) + " " + str(cur.rowcount))
		
		if check:
			row = cur.fetchone()
			if row:
				authdb.close()
				web.debug(row)
				web.debug(session)
				#session = session_default
				session.uid = row[0]
				session.user = username
			
				# if we found one, exit
				return '{"success": true}'
		
		authdb.close()
		
		
		# if not found check against ldap
		usbauth.init(
			authdn = "CN=MUANA,OU=GenericMove,OU=Users,OU=USB,DC=ms,DC=uhbs,DC=ch",
			authpw = "anaana",
			baseDN = "ou=USB,dc=ms,dc=uhbs,dc=ch",
			host = "ms.uhbs.ch",
		)
		
		emp = usbauth.check(username, password)
		if (emp and emp["lockoutTime"] == None):
			#session = session_default
			session.uid = emp["employeeNumber"]
			session.user = username
			session.email = emp["email"]
			return '{"success": true}'
		
		return '{"success": false}'

class checklist_feedback(webctx):
	reason = [
		u"Patientenidentifikation",
		u"Markierung gemäss USB-Standard",
		u"Pflege- / Patientendokumentation",
		u"Letzte Nahrung (>6h)",
		u"Zahnprotesen, Piercing, Hörgerät, Schmuck inkl. Ehering, Kleidung",
		u"Dekubitus vorhanden",
		u"Patient zum Wasserlösen aufgefordert",
		u"Isolationspflichtiger Patient"
	]
	
	def GET(self):

		conn, cursor = oraconn()
		
		today = datetime.datetime.now() # + datetime.timedelta(days=1)
		
		sql =  """SELECT o.ID, o.STMNAME, o.STMVORNAME, substr(o.OPTEXT, 0, 50)
		FROM DATO_OP o
		WHERE o.OPDATUM = '""" + str(today.strftime("%Y%m%d")) +  """'
			AND o.TSCANCEL IS NULL AND (o.DEL IS NULL OR o.DEL = 'N')
		ORDER BY o.STMNAME, o.STMVORNAME"""
		
		#web.debug(sql)
		#web.debug(conn)
		#web.debug(cursor)
		
		res = []
		
		try:
			cursor.execute(sql)
		except Exception, e:
			web.debug(e)
			return "database error"
		
		ops = []
		for row in cursor:
			ops.append(row)
		
		return web.template.render('template').checklist_feedback(ops, self.reason)
	
	def POST(self):
		post = web.input()
		conn, cursor = oraconn()
		
		reason = ""
		
		for p in post:
			web.debug(p)
			if p[0] == 'r':
				reason += u" - " + self.reason[int(post[p])] + u"\n"

		sql =  """SELECT o.STMNAME, o.STMVORNAME, o.FACHDISZI
		FROM DATO_OP o
		WHERE o.ID = %d""" % int(post["op"])
		
		try:
			cursor.execute(sql)
		except Exception, e:
			web.debug(e)
			return "database error"
		
		pat = ""
		fach = ""
		for row in cursor:
			pat = row[0] + " " + row[1]
			fach = row[2]
		
		to = "Stephan.Schaerer@usb.ch"		
		if fach == "MD" or fach == "MK":
			to = "Anja.Ulrich@usb.ch"
		if fach == "AU" or fach == "FG" or fach == "FK" or fach == "HN":
			to = "Esther.Sackmann@usb.ch"
		
		if fach == "XX" or fach == "AN":
			return "Empfänger konnte nicht ermittelt werden."
		
		#web.debug(post["bemerkung"])
		
		body = u"""Guten Tag

Dieses Mail ist eine Rückmeldung im Zusammenhang mit der Präoperativen Checkliste an die entsprechend verantwortlichen FachbereichsleiterIn. Bitte leiten Sie dies in entsprechender Weise den direkt verantwortlichen Personen (z.B. Stationsleitung) weiter. So dass der Prozess in Zukunft eingehalten werden kann.

Patient: %s

Folgende Punkte wurden nicht vollständig erfüllt:
~~~~

Bemerkung:
%s

mit bestem Dank für Ihre Mithilfe zu Gunsten der Patientensicherheit.

		""" % (pat.decode('utf8'), post["bemerkung"])
		body = body.replace(u"~~~~", reason)
		
		import smtplib
		import email.utils
		from email.mime.text import MIMEText
		from email.mime.multipart import MIMEMultipart

		# Create the message
		eml_from = 'Peter.Mueller@usb.ch'
		# eml_to  = 'simon.wunderlin@usb.ch'
		eml_to   = to
		eml_bcc  = 'siegfried.batzer@usb.ch'
		
		msg = MIMEMultipart('alternative')
		msg['To'] = email.utils.formataddr(('Recipient', eml_to))
		msg['From'] = email.utils.formataddr(("OP Koordination", eml_from))
		msg['Bcc'] = email.utils.formataddr(('Kontrolle', eml_bcc))
		msg['Subject'] = 'Feedback Praeoperative Checkliste'
		textpart = MIMEText(body.encode('utf-8'), 'plain', 'utf-8')
		msg.attach(textpart)
		
		server = smtplib.SMTP(config.smtp)
		#server.set_debuglevel(True) # show communication with the server
		
		try:
			server.sendmail(eml_from, [eml_to] + [eml_bcc], msg.as_string())
		finally:
			server.quit()
		
		return "Versendet"

class checklist_feedback_stat(webctx):
	reason = [
		u"Patientenidentifikation",
		u"Markierung gemäss USB-Standard",
		u"Pflege- / Patientendokumentation",
		u"Letzte Nahrung (>6h)",
		u"Zahnprotesen, Piercing, Hörgerät, Schmuck inkl. Ehering, Kleidung",
		u"Dekubitus vorhanden",
		u"Patient zum Wasserlösen aufgefordert",
		u"Isolationspflichtiger Patient",
		u"OP ohne Information der Station verschoben"
	]
	
	def GET(self):

		conn, cursor = oraconn()
		
		today = datetime.datetime.now() # + datetime.timedelta(days=1)
		
		sql =  """SELECT o.ID, o.STMNAME, o.STMVORNAME, substr(o.OPTEXT, 0, 50)
		FROM DATO_OP o
		WHERE o.OPDATUM = '""" + str(today.strftime("%Y%m%d")) +  """'
			AND o.TSCANCEL IS NULL AND (o.DEL IS NULL OR o.DEL = 'N')
		ORDER BY o.STMNAME, o.STMVORNAME"""
		
		#web.debug(sql)
		#web.debug(conn)
		#web.debug(cursor)
		
		res = []
		
		try:
			cursor.execute(sql)
		except Exception, e:
			web.debug(e)
			return "database error"
		
		ops = []
		for row in cursor:
			ops.append(row)
		
		return web.template.render('template').checklist_feedback_station(ops, self.reason)
	
	def POST(self):
		post = web.input()
		conn, cursor = oraconn()
		
		reason = ""
		
		for p in post:
			web.debug(p)
			if p[0] == 'r':
				reason += u" - " + self.reason[int(post[p])] + u"\n"
		
		# find patient
		sql =  """SELECT o.STMNAME, o.STMVORNAME, o.FACHDISZI
		FROM DATO_OP o
		WHERE o.ID = %d""" % int(post["op"])
		
		try:
			cursor.execute(sql)
		except Exception, e:
			web.debug(e)
			return "database error"
		
		pat = ""
		fach = ""
		for row in cursor:
			pat = row[0] + " " + row[1]
			fach = row[2]
		
		# finde operateur email
		sql = """
		SELECT p.id, p.email
		FROM CONF_PERSONAL p
		WHERE p.id in (
			(
				SELECT o.chir1id as id
				FROM DATO_OP o
				WHERE o.ID = %d
			) UNION (
				SELECT o.chir2id as id
				FROM DATO_OP o
				WHERE o.ID = %d
	
			) UNION (
				SELECT o.chir3id as id
				FROM DATO_OP o
				WHERE o.ID = %d
	
			) UNION (
				SELECT o.chir4id as id
				FROM DATO_OP o
				WHERE o.ID = %d
	
			)
		)
		""" % (int(post["op"]), int(post["op"]), int(post["op"]), int(post["op"]))
		
		try:
			cursor.execute(sql)
		except Exception, e:
			web.debug(e)
			return "database error"
		
		to_lst = []
		for row in cursor:
			to_lst.append(row[1])
		
		# Debug
		#to_lst = ["simon.wunderlin@usb.ch"]
		
		"""
		to = "Stephan.Schaerer@usb.ch"		
		if fach == "MD" or fach == "MK":
			to = "Anja.Ulrich@usb.ch"
		if fach == "AU" or fach == "FG" or fach == "FK" or fach == "HN":
			to = "Anja.Ulrich@usb.ch"
		
		if fach == "XX" or fach == "AN":
			return "Empfänger konnte nicht ermittelt werden."
		"""
		
		
		#web.debug(post["bemerkung"])
		
		body = u"""Guten Tag

Dieses Mail ist eine Rückmeldung im Zusammenhang mit der Präoperativen Checkliste an die entsprechend verantwortlichen FachbereichsleiterIn. Bitte leiten Sie dies in entsprechender Weise den direkt verantwortlichen Personen (z.B. Stationsleitung) weiter. So dass der Prozess in Zukunft eingehalten werden kann.

Patient: %s

Folgende Punkte wurden nicht vollständig erfüllt:
~~~~

Bemerkung:
%s

mit bestem Dank für Ihre Mithilfe zu Gunsten der Patientensicherheit.

		""" % (pat.decode('utf8'), 
			post["bemerkung"])
		web.debug(pat)
		body = body.replace(u"~~~~", reason)
		
		import smtplib
		import email.utils
		from email.mime.text import MIMEText
		from email.mime.multipart import MIMEMultipart

		# Create the message
		eml_from = 'Stephan.Schaerer@usb.ch'
		#eml_to   = to
		eml_bcc  = 'Stephan.Schaerer@usb.ch'

		#eml_to  = 'simon.wunderlin@usb.ch'
		#eml_bcc  = 'simon.wunderlin@usb.ch'
		
		msg = MIMEMultipart('alternative')
		#msg['To'] = email.utils.formataddr(('Recipient', eml_to))
		#to_lst = ["simon.wunderlin@usb.ch", "mq_ana_it@usb.ch"]
		msg['To'] = ",".join(to_lst)
		msg['From'] = email.utils.formataddr(("OP Koordination", eml_from))
		msg['Bcc'] = email.utils.formataddr(('Kontrolle', eml_bcc))
		msg['Subject'] = 'Feedback Praeoperative Checkliste'
		textpart = MIMEText(body.encode('utf-8'), 'plain', 'utf-8')
		msg.attach(textpart)
		
		server = smtplib.SMTP(config.smtp)
		#server.set_debuglevel(True) # show communication with the server
		
		try:
			server.sendmail(eml_from, to_lst + [eml_bcc], msg.as_string())
		finally:
			server.quit()
		
		return "Versendet"


class index(webctx):
	""" Serve index page """
	def GET(self):
		if not self.auth_check():
			return self.render().login()
			
		#web.debug(auth_check)
		#web.debug(session)
		
		render = web.template.render('template')
		return render.index()
		#return out

class ha(webctx):
	""" Serve index page """
	def GET(self):
		if not self.auth_check():
			return self.render().login()
		
		conn, cursor = oraconn()
		
		default_dt = datetime.datetime.now() + datetime.timedelta(days=1)
		
		datum = web.input(datum=default_dt.strftime("%d.%m.%Y")).datum
		web.debug(datum)
		
		try:
			dt = datetime.datetime.strptime(datum, '%d.%m.%Y')
		except:
			return "Failed to parse input date"
		
		sql =  """SELECT o.OPTEXT, o.STMNAME, o.STMVORNAME, TO_CHAR(TO_DATE(o.STMGEBDAT, 'YYYYMMDD'), 'DD.MM.YYYY'), o.OPSAAL, o.OPSEQ, o.ID,
					 h.VENFLON_R, h.VENFLON_L, h.INFUSION_RV, h.INFUSION_3H, BEMERKUNG

		FROM DATO_OP o LEFT JOIN DATO_HOLDINGAREA h ON (o.ID = h.OPID)

		WHERE o.OPDATUM = '""" + str(dt.strftime("%Y%m%d")) +  """'
			AND UPPER(SUBSTR(o.OPTEXT, 0, 2)) = 'HA'
			AND o.TSCANCEL IS NULL AND (o.DEL IS NULL OR o.DEL = 'N')
		ORDER BY o.OPSAAL, o.OPSEQ"""
		
		web.debug(sql)
		#web.debug(conn)
		#web.debug(cursor)
		
		res = []
		
		try:
			cursor.execute(sql)
		except Exception, e:
			web.debug(e)
			return "database error"
		
		alpha = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
		
		for row in cursor:
			if row[0][2].lower() not in alpha:
			 res.append(row)
		
		# get daily data
		sql = "SELECT OA, AA, PFL FROM DATO_HOLDINGAREA_STAFF WHERE DATUM = TO_DATE('" + str(dt.strftime("%Y%m%d")) +  "', 'YYYYMMDD')"
		
		try:
			cursor.execute(sql)
		except Exception, e:
			web.debug(e)
			return "database error"
		
		staff = {"OA": "", "AA": "", "PFL": "85244"}
		for row in cursor:
			staff = {"OA": row[0], "AA": row[1], "PFL": row[2]}
		
		web.debug(res)
		
		return self.render().ha(res, staff, dt.strftime("%d.%m.%Y"))

	def POST(self):
		raw_data = web.data()
		conn, cursor = oraconn()
		
		web.header('Content-Type', 'application/json')
		
		try:
			data = json.loads(raw_data)
		except:
			return '{"success": false, "message": "Failed to decode json string"}'
		
		try:
			data["ma"]["datum"] = datetime.datetime.strptime(data["ma"]["datum"], '%d.%m.%Y')
		except:
			return "Failed to parse input date"

		#web.debug(data["ma"])
		
		# update metadata
		
		sql = "SELECT DATUM FROM DATO_HOLDINGAREA_STAFF WHERE DATUM = TO_DATE('%s', 'YYYYMMDD')" % \
		       data["ma"]["datum"].strftime('%Y%m%d')
		web.debug(sql)
		try:
			cursor.execute(sql)
		except Exception, e:
			#web.debug(e)
			return '{"success": false, "message": "Failed to query metadata in database"}'

		count = 0
		for r in cursor:
			count += 1

		if count: # update
			sql = """UPDATE DATO_HOLDINGAREA_STAFF
				     SET AA='%s',
				         OA='%s',
				         PFL='%s'
				     WHERE DATUM = TO_DATE('%s', 'YYYYMMDD')""" % \
			(data["ma"]["aa"], data["ma"]["oa"], data["ma"]["pfl"], data["ma"]["datum"].strftime('%Y%m%d'))
		else:
			sql = """INSERT INTO DATO_HOLDINGAREA_STAFF (AA, OA, PFL, DATUM) VALUES
				       ('%s', '%s', '%s',  TO_DATE('%s', 'YYYYMMDD')) """ % \
			(data["ma"]["aa"], data["ma"]["oa"], data["ma"]["pfl"], data["ma"]["datum"].strftime('%Y%m%d'))
				
		try:
			cursor.execute(sql)
			conn.commit()
		except Exception, e:
			web.debug(sql)
			web.debug(e)
			return '{"success": false, "message": "Failed to update metadata in database"}'
		
		for row in data["grid"]:
			#web.debug(row)
			
			# check if all False
			if row["INFUSION_3H"] == False and row["INFUSION_RV"] == False and \
			   row["VENFLON_L"] == False and row["VENFLON_R"] == False and row["BEMERKUNG"] == "":
				
				# all False,: delete db record
				sql = "DELETE FROM DATO_HOLDINGAREA WHERE OPID = " + str(row["id"])
				#web.debug(sql)
				try:
					cursor.execute(sql)
					conn.commit()
				except Exception, e:
					web.debug(e)
					return '{"success": false, "message": "Failed to delete in database"}'
			
			else:
				# check if record exists
				sql = "SELECT OPID FROM DATO_HOLDINGAREA WHERE OPID = " + str(row["id"])
				#web.debug(sql)
				try:
					cursor.execute(sql)
				except Exception, e:
					#web.debug(e)
					return '{"success": false, "message": "Failed to query in database"}'
				
				count = 0
				for r in cursor:
					count += 1
				
				if count:
					# update
					#web.debug(row)
					sql = """UPDATE DATO_HOLDINGAREA SET 
					         VENFLON_R = """ + str(int(row["VENFLON_R"])) + """,
					         VENFLON_L = """ + str(int(row["VENFLON_L"])) + """,
					         INFUSION_RV = """ + str(int(row["INFUSION_RV"])) + """,
					         INFUSION_3H = """ + str(int(row["INFUSION_3H"])) + """,
					         BEMERKUNG = '""" + unicode(row["BEMERKUNG"]).replace("'", "''") + """'
					         WHERE OPID = """ + str(row["id"])
					#web.debug(sql)
					try:
						#cursor.prepare(sql)
						cursor.execute(sql)
						conn.commit()
					except Exception, e:
						web.debug(e)
						return '{"success": false, "message": "Failed to update in database"}'
				
				else:
					# insert
					sql = """INSERT INTO DATO_HOLDINGAREA 
					         (VENFLON_R, VENFLON_L, INFUSION_RV, INFUSION_3H, BEMERKUNG, OPID) VALUES ( """ + \
					         unicode(int(row["VENFLON_R"])) + ", " + unicode(int(row["VENFLON_L"])) + ", " + \
					         unicode(int(row["INFUSION_RV"])) + ", " + unicode(int(row["INFUSION_3H"])) + ", '" + unicode(row["BEMERKUNG"]).replace("'", "''") + \
					         "', " + unicode(int(row["id"])) + ")"
					#web.debug(sql)
					try:
						cursor.execute(sql)
						conn.commit()
					except Exception, e:
						#web.debug(e)
						return '{"success": false, "message": "Failed to insert in database"}'
			conn.commit()
		
		return '{"success": true}'

class image(webctx):
	no_auth = True
	""" Serve image, this method requires not authentication """
	def GET(self):
		filename = "static/py.png"
		web.header('Content-Type', 'image/png')
		web.header('Content-Length', os.path.getsize(filename))
		import datetime
		t = datetime.datetime.fromtimestamp(os.path.getmtime(filename))
		#strdate = t.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
		web.http.lastmodified(t)
		fp = open(filename, "r")
		yield fp.read()
		fp.close()
		
		return

class env(webctx):
	""" display environment variables """
	def GET(self):
		if not self.auth_check():
			return self.render().login()
		
		out = {}
		for property, value in vars(web.ctx).iteritems():
			out[property] = value
		
		return self.render().env(out)

class json1(webctx):
	""" Serve json example page (using JQuery)"""
	def GET(self):
		if not self.auth_check():
			return self.render().login()
			
		#render = web.template.render('template')
		return self.render().json1()
		#return out
	
	def POST(self):
		if not self.auth_check():
			return self.render().login()
		
		post = web.input()
		web.header('Content-Type', 'application/json')
		try:
			i1 = int(post.int1)
			i2 = int(post.int2)
			res = i1 + i2
		except:
			return '{"error": 1}'
		
		return '{"error": 0, "i1": '+str(i1)+', "i2": '+str(i2)+', "res": '+str(res)+'}'
		
class json2(webctx):
	""" Serve json example page (100% VanillaJS)"""
	def GET(self):
		if not self.auth_check():
			return self.render().login()
		
		render = web.template.render('template')
		return render.json2()
	
	def POST(self):
		if not self.auth_check():
			return self.render().login()
		
		web.header('Content-Type', 'application/json')
		try:
			post = json.loads(web.data())
			i1 = int(post["int1"])
			i2 = int(post["int2"])
			res = i1 + i2
			print str(res)
		except:
			return '{"error": 1}'
		
		return '{"error": 0, "i1": '+str(i1)+', "i2": '+str(i2)+', "res": '+str(res)+'}'

