#!/usr/bin/env python
# -*- coding: utf8 -*-
"""
This file provides lookup and authentication methods for AD users from the 
ms.uhbs.ch AD directory.

The file provides 2 main functions:
	
	lookup(username|emailaddr)
		checks if a user exists. all active new and old emailaddresses are avialble 
		keys which is sought for.
	
	check(username|emailaddr, password)
		will try to authenticate with the provided credentials. returns dictionary 
		of userinformation upon success, False if authentication failes and None 
		if the Object could not be found.
	
	Both methods print a json string, with the following attributes, to stdout:
		{
			"dn" : None,          # ldap distinguished name
			"username": None,     # the login name
			"phone": None,        # phone number if any (cordless preferred)
			"email": None,        # primary email address
			"firstname": None,    # person's first name 
			"lastname": None,     # person's last name 
			"idmid": None,        # identity management id
			"employeeNumber": None, # employee id (Same as on the backside of the batch)
			"memberOf": [],       # list of group membership cn
			"lockoutTime": None   # datetime of lockout, None of not locked
		}
"""


import ldap, sys, json
from datetime import datetime

class usbauth(object):
	@staticmethod
	def _json_serial(obj):
		"""JSON serializer for datetime"""

		if isinstance(obj, datetime):
			serial = obj.isoformat()
			return serial
			raise TypeError ("Type not serializable")

	@staticmethod
	def winfiletime2datetime(winfiletime):
		""" convert NT Filesystem Time to datetime """
		#print winfiletime
		EPOCH_AS_FILETIME = 116444736000000000
		HUNDREDS_OF_NANOSECONDS = 10000000
		return datetime.fromtimestamp((int(winfiletime) - EPOCH_AS_FILETIME) / HUNDREDS_OF_NANOSECONDS)
	
	
	""" lookup and authentication library """
	@property
	def lastobj(self):
		return self.__lastobj
	
	# configuration
	baseauth = {
		"dn": None,
		"pw": None
	}
	baseDN = None
	search_property = "sAMAccountName"
	host = None
	
	def __init__(self, authdn=None, authpw=None, baseDN=None, host=None):
		""" setup ldap connection
		
			authdn  the distinguished name used for simple authentication
			authpw  password for simple authentication
			baseDN  Search base (using subtree search)
			host    LDAP hostname or IP
		"""
		if (authdn): self.baseauth["dn"] = authdn
		if (authpw): self.baseauth["pw"] = authpw

		if (baseDN): self.baseDN = baseDN
		if (host): self.host = host
		
		
		self.__conn = None
		self.__lastobj = None
		
		# open an ldap connection for searching 
		self.__conn = ldap.open(self.host)
		self.__conn.protocol_version = ldap.VERSION3
		self.__conn.simple_bind_s(self.baseauth["dn"], self.baseauth["pw"])

	def auth(self, username, pw):
		""" check password, retruns True on success """
		
		if not pw:
			return False
		
		try:
			userdn = self.lookup(username)
			if not userdn:
				return userdn
			
			l = ldap.open(self.host)
			l.protocol_version = ldap.VERSION3
			l.simple_bind_s(userdn, pw)
			
		except ldap.LDAPError, e:
			return False # e.message["desc"]
		
		return True
	
	def lookup(self, username):
		""" returns the DN of an object with the sAMAccountName == username 
		
		will check if the username contains an "@", if so search for email address 
		instead of account name.
		
		returns the DN as String or None if not found, False on error
		"""
		
		is_email = False
		try:
			if username.index("@") > 0:
				is_email = True
				self.search_property = "mail"
		except ValueError, e:
			pass
		
		self.__lastobj = None
		ldap_result_id = self.__conn.search(self.baseDN, 
		                                    ldap.SCOPE_SUBTREE, 
		                                    self.search_property+"="+username, 
		                                    None)
		result_type, result_data = self.__conn.result(ldap_result_id, 0)
		#print result_type, result_data
		
		if (result_type != 100):
			if not is_email:
				return None
			
			# if this is an email addr and we didn't find it, try to find an 
			# legacy emailaddress
			self.search_property = "proxyAddresses"
			ldap_result_id = self.__conn.search(self.baseDN, 
				                                  ldap.SCOPE_SUBTREE, 
				                                  self.search_property+"=smtp:"+username, 
				                                  None)
			result_type, result_data = self.__conn.result(ldap_result_id, 0)
			if (result_type != 100):
				return None
		
		#print result_type
		try:
			self.__lastobj = result_data[0]
			#print self.__lastobj
			return self.__lastobj[0]
		except:
			return None
		
		return None
	
	def info(self, obj):
		""" Display data of a user
		
		do a self.lookup first
		
		"""
		ret = {
			"dn" : None,
			"username": None,
			"phone": None,
			"email": None,
			"firstname": None,
			"lastname": None,
			"idmid": None,
			"employeeNumber": None,
			"memberOf": [],
			"lockoutTime": None,
			"personalTitle": None
		}
		
		try: ret["dn"] = obj[0]; 
		except: pass
		try: ret["username"] = obj[1]["sAMAccountName"][0]; 
		except: pass
		try: 
			ret["phone"] = obj[1]["telephoneNumber"][0];
			if obj[1]["otherTelephone"][0] != "":
				ret["phone"] = obj[1]["otherTelephone"][0];
		
		except: pass
		try: ret["email"] = obj[1]["mail"][0]; 
		except: pass
		try: ret["firstname"] = obj[1]["givenName"][0]; 
		except: pass
		try: ret["lastname"] = obj[1]["sn"][0]; 
		except: pass
		try: ret["idmid"] = int(obj[1]["employeeID"][0]); 
		except: pass
		try: ret["employeeNumber"] = int(obj[1]["employeeNumber"][0]); 
		except: pass
		try: ret["memberOf"] = obj[1]["memberOf"]; 
		except: pass
		try: ret["personalTitle"] = obj[1]["personalTitle"][0]; 
		except: pass

		try: 
			if int(obj[1]["lockoutTime"][0]) > 0:
				#print obj[1]["lockoutTime"][0]
				ret["lockoutTime"] = usbauth.winfiletime2datetime(obj[1]["lockoutTime"][0])
		except: 
			pass
		
		return ret
	
	@staticmethod
	def main(username, password):
		""" main function """
		
		try:
			a = usbauth()
		except ldap.LDAPError, e:
			print "Failed to connect to ldap, with message: %s" % (e.message["desc"])
			return False
		ret = a.auth(username, password)
		if ret != True:
			return ret
		
		return a.info(a.__lastobj)

def init(authdn=None, authpw=None, baseDN=None, host=None):
		
		if (authdn): usbauth.baseauth["dn"] = authdn
		if (authpw): usbauth.baseauth["pw"] = authpw

		if (baseDN): usbauth.baseDN = baseDN
		if (host): usbauth.host = host

def check(username, pw):
	return usbauth.main(username, pw)

def lookup(username):
	a = usbauth()
	obj = a.lookup(username)
	if (obj):
		return a.info(a.lastobj)
	else:
		return None

if __name__ == "__main__":
	usage = """Usage: auth.py <username|emailaddr> [password]
	
When only a username|emailaddr is provided, then we do a lookup of the user via ldap.

If username and password is provided, we do an authentication.

Exit code 
	  0 success
	  1 not found
	  2 wrong username/password. 
	127 argument error
"""

	# check how many arguments we've got.	
	
	# setup ldap connection
	init(
		authdn = "CN=MUANA,OU=GenericMove,OU=Users,OU=USB,DC=ms,DC=uhbs,DC=ch",
		authpw = "anaana",
		baseDN = "ou=USB,dc=ms,dc=uhbs,dc=ch",
		host = "ms.uhbs.ch",
	)
	
	# lokup user
	if len(sys.argv) == 2:
		emp = lookup(sys.argv[1])
		if (emp == None):
			sys.exit(1)
		
		print json.dumps(emp, sort_keys=True, indent=4, separators=(',', ': '), default=usbauth._json_serial)
		sys.exit(0)
	
	# authenticate user
	elif len(sys.argv) == 3:
		emp = check(sys.argv[1], sys.argv[2])
		#print emp
		if (not emp):
			#print emp
			if emp == False:
				sys.stderr.write("Failed to authenticate\n")
				sys.exit(2)
			else:
				sys.stderr.write("User not found\n")
				sys.exit(1)
		
		print json.dumps(emp, sort_keys=True, indent=4, separators=(',', ': '), default=usbauth._json_serial)
		sys.exit(0)
	
	# argument error
	else:
		print usage
	
	sys.exit(127)

