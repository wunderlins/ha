#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
from datetime import *
import cx_Oracle

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
	

def dt2reverse(dt):
	s = str(dt.year)
	if dt.month < 10:
		s += "0"
	s += str(dt.month)
	if dt.day < 10:
		s += "0"
	s += str(dt.day)
	
	return s

def format_result(data):
	print "Hour;Count"
	for e in data:
		print str(e) + ";" + str(data[e])


def distribution(start, end, result, cur):
	s_start = dt2reverse(start)
	s_end   = dt2reverse(end)
	
	#print s_end + " " + s_start
	
	sql = """SELECT z.TSVORB, z.TSVERLEGT
	      FROM DATO_ZEITEN z LEFT JOIN DATO_OP o ON z.OPID = o.ID
	      WHERE z.OPDATUM >= TO_DATE('%s', 'YYYYMMDD')
	        AND z.OPDATUM <= TO_DATE('%s', 'YYYYMMDD')
	      	AND o.EXPORTFLAG = '4'
	      """ % (s_start, s_end)
	
	#print sql
	
	try:
		cur.execute(sql)
	except Exception, e:
		print "database error"
		sys.exit(1)
	
	total = 0;
	for row in cur:
		try:
			hs = int(row[0].hour)
			he = int(row[1].hour)
		except:
			continue
		
		#print str(hs) + " " + str(he)
		for e in hours:
			#sys.stdout.write(" " + str(e))
			if hs <= int(e) and he >= int(e):
				#sys.stdout.write("+")
				hours[e] += 1
				total += 1
		#sys.stdout.write("\n")
	
	#return result

if __name__ == "__main__":
	# connect
	con, cur = oraconn()
	
	hours = {0: 0, 1: 0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0, 9:0, 10:0, 11:0, 12:0, 
	         13:0, 14:0, 15:0, 16:0, 17:0, 18:0, 19:0, 20:0, 21:0, 22:0, 23:0}
	
	
	
	start = datetime(2015, 1, 5)
	while True:
		if start.year > 2015:
			break
			
		s = start+timedelta(days=6)
		e = start+timedelta(days=6)
		#sys.stdout.write(str(s) + " ")
		#sys.stdout.write(str(e) + "\n")
		distribution(s, e, hours, cur)
		start = start+timedelta(days=7)
		
	format_result(hours)
	
	
	"""
	distribution(date(2016, 5, 2), date(2016, 5, 8), hours, cur)
	distribution(date(2016, 4, 25), date(2016, 5, 1), hours, cur)
	print hours
	"""
	
	'''
	
	s_start = dt2reverse(start)
	s_end   = dt2reverse(end)
	
	#print s_end + " " + s_start
	
	sql = """SELECT z.TSSCHNITT, z.TSNAHT
	      FROM DATO_ZEITEN z LEFT JOIN DATO_OP o ON z.OPID = o.ID
	      WHERE z.OPDATUM >= TO_DATE('%s', 'YYYYMMDD')
	        AND z.OPDATUM <= TO_DATE('%s', 'YYYYMMDD')
	      	AND o.EXPORTFLAG = '4'
	      """ % (s_start, s_end)
	
	print sql
	
	try:
		cur.execute(sql)
	except Exception, e:
		print "database error"
		sys.exit(1)
	
	total = 0;
	for row in cur:
		try:
			hs = int(row[0].hour)
			he = int(row[1].hour)
		except:
			continue
		
		print str(hs) + " " + str(he)
		for e in hours:
			sys.stdout.write(" " + str(e))
			if hs <= int(e) and he >= int(e):
				sys.stdout.write("+")
				hours[e] += 1
				total += 1
		sys.stdout.write("\n")
			
	print hours
	print total
	'''
