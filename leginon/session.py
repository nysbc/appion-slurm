'''
This modules defines functions for creating sessions and reserving a session
name while in the process of creating a session.
'''

import os.path
import time

from pyami import moduleconfig

import leginon.leginondata
import leginon.projectdata
import leginon.leginonconfig
import leginon.project

projectdata = leginon.project.ProjectData()

reserved = None

def makeReservation(name):
	global reserved
	if reserved and reserved.name == name:
		return
	reserved = Reservation(name)

def cancelReservation():
	global reserved
	if reserved:
		reserved.cancel()
		reserved = None

class ReservationFailed(Exception):
	pass

class Reservation(object):
	'''reserves a name in __init__, cancels reservation in __del__'''
	def __init__(self, name):
		self.name = None
		if not self.create(name):
			raise ReservationFailed('name already reserved: %s' % (name,))
		self.name = name

	def __del__(self):
		self.cancel()

	def create(self, name):
		'''
		Try to reserve a session name.
		Return True if reservation is successful.
		Return False if it is already used, or reserved by another process.
		'''
		## fail reservation if name exists in SessionData
		sessiondata = leginon.leginondata.SessionData(name=name)
		sessions = sessiondata.query()
		if sessions:
			return False
	
		## fail if reservation found in SessionReservationData
		sessionres = leginon.leginondata.SessionReservationData(name=name)
		sessionres = sessionres.query(results=1)
		if sessionres and sessionres[0]['reserved']:
			return False
	
		## make new reservation
		sessionres = leginon.leginondata.SessionReservationData(name=name, reserved=True)
		sessionres.insert(force=True)
		return True

	def cancel(self):
		if self.name is None:
			return
		sessionres = leginon.leginondata.SessionReservationData(name=self.name, reserved=False)
		sessionres.insert(force=True)
		self.name = None

def getSessionPrefix():
	session_name = '<cannot suggest a name>'
	try:
		prefix = moduleconfig.getConfigured('leginon_session.cfg', 'leginon')['name']['prefix']
	except IOError as e:
		prefix = ''
	except KeyError:
		raise ValueError('session prefix needs to be in "name" section and item "prefix"')
	return prefix

def suggestName():
	prefix = getSessionPrefix()
	for suffix in 'abcdefghijklmnopqrstuvwxyz':
		maybe_name = prefix + time.strftime('%y%b%d'+suffix).lower()
		try:
			makeReservation(maybe_name)
		except ReservationFailed, e:
			continue
		else:
			session_name = maybe_name
			break
	return session_name

def createSession(user, name, description, directory, holder=None):
	imagedirectory = os.path.join(leginon.leginonconfig.unmapPath(directory), name, 'rawdata').replace('\\', '/')
	framedirectory = leginon.ddinfo.getRawFrameSessionPathFromSessionPath(imagedirectory)
	initializer = {
		'name': name,
		'comment': description,
		'user': user,
		'image path': imagedirectory,
		'frame path': framedirectory,
		'hidden': False,
		'holder': holder,
	}
	return leginon.leginondata.SessionData(initializer=initializer)

def linkSessionProject(sessionname, projectid):
	if projectdata is None:
		raise RuntimeError('Cannot link session, not connected to database.')
	projq = leginon.projectdata.projects()
	projdata = projq.direct_query(projectid)
	projeq = leginon.projectdata.projectexperiments()
	sessionq = leginon.leginondata.SessionData(name=sessionname)
	sdata = sessionq.query()
	projeq['session'] = sdata[0]
	projeq['project'] = projdata
	return projeq

def getSessions(userdata, n=None):
	'''
	SetupWizard getSessions. allow filtering by prefix and limit returned sessions to n
	'''
	prefix = getSessionPrefix()
	names = []
	sessiondatalist = []
	multiple = 1
	while n is None or (len(names) < n and multiple < 10):
		sessionq = leginon.leginondata.SessionData(initializer={'user': userdata})
		if n is None:
			sessiondatalist = sessionq.query()
		else:
			sessiondatalist = sessionq.query(results=n*multiple)
		for sessiondata in sessiondatalist:
			# back compatible where there is no hidden field or as None, not False.
			if sessiondata['hidden'] is True:
				continue
			name = sessiondata['name']
			if prefix and not name.startswith(prefix):
				continue
			if name is not None and name not in names:
				names.append(name)
		multiple += 1
		if n is None:
			break
	return names, sessiondatalist

def hasGridHook():
	try:
		server_configs = moduleconfig.getConfigured('gridhook.cfg', 'leginon')
	except IOError as e:
		return False
	return True

def createGridHook(session_dict, project_dict):
	from leginon import gridserver
	return gridserver.GridHookServer(session_dict,project_dict)
