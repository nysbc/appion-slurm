#!/usr/bin/env python

import node
import data
import event
import nodeclassreg
import calllauncher
import time


class Launcher(node.Node):
	def __init__(self, id, nodelocations = {}, port = None):
		node.Node.__init__(self, id, nodelocations, tcpport=port)

		self.addEventInput(event.LaunchEvent, self.handleLaunch)
		self.addEventInput(event.UpdateNodeClassesEvent, self.publishNodeClasses)
		self.addEventOutput(event.NodeClassesPublishEvent)
		self.caller = calllauncher.CallLauncher()
		print 'launcher id: %s' % (self.id,)
		self.print_location()
		self.start()

	def addManager(self, loc):
		self.managerclient = self.clientclass(self.ID(), loc)
		e = event.NodeAvailableEvent(self.ID(), self.location(),
					self.__class__.__name__)
		self.outputEvent(ievent=e, wait=1)
		time.sleep(1)
		self.publishNodeClasses()

	def main(self):
		pass

	def publishNodeClasses(self):
		reload(nodeclassreg)
		nodeclassnames = nodeclassreg.getNodeClassNames()
		d = data.NodeClassesData(self.ID(), nodeclassnames)
		self.publish(d, event.NodeClassesPublishEvent)

	def handleLaunch(self, launchevent):
		# unpack event content
		newproc = launchevent.content['newproc']
		targetclass = launchevent.content['targetclass']
		args = launchevent.content['args']
		kwargs = launchevent.content['kwargs']

		# get the requested class object
		nodeclass = nodeclassreg.getNodeClass(targetclass)

		## thread or process
		if newproc:
			self.caller.launchCall('fork',nodeclass,args,kwargs)
		else:
			self.caller.launchCall('thread',nodeclass,args,kwargs)

	def defineUserInterface(self):
		nint = node.Node.defineUserInterface(self)

		ref = self.registerUIMethod(self.uiRefresh, 'Refresh', ())

		self.registerUISpec('Launcher: %s' % (self.id,), (nint, ref))

	def uiRefresh(self):
		self.publishNodeClasses()
		return ''

	def launchThread(self):
		pass

	def launchProcess(self):
		pass

if __name__ == '__main__':
	import sys, socket

	myhost = socket.gethostname()
	myid = (myhost,)

	managerlocation = {}
	try:
		managerlocation['hostname'] = sys.argv[1]
		try:
			managerlocation['TCP port'] = int(sys.argv[2])
			#managerlocation['UNIX pipe filename'] = str(sys.argv[3])
			m = Launcher(myid, {'manager': managerlocation})
		except IndexError:
			m = Launcher(myid, {}, int(sys.argv[1]))
	except IndexError:
		try:
			m = Launcher(myid, {}, 55555)
		except:
			m = Launcher(myid, {})

