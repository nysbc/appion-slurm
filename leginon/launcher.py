#!/usr/bin/env python

import signal
import node
import event
import threading
import common
import calllauncher


class Launcher(node.Node):
	def __init__(self, id, managerlocation = None):
		node.Node.__init__(self, id, managerlocation)

		self.addEventInput(event.LaunchEvent, self.handleLaunch)
		self.caller = calllauncher.CallLauncher()
		self.main()

	def addManager(self, loc):
		'''
		Node uses NodeAvailableEvent 
		This uses LauncherAvailableEvent
		'''
		self.managerloc = loc
		self.addEventClient('manager', loc)
		self.announce(event.LauncherAvailableEvent(self.ID()))

	def main(self):
		self.interact()

	def handleLaunch(self, launchevent):
		# unpack event content
		newproc = launchevent.content['newproc']
		targetclass = launchevent.content['targetclass']
		args = launchevent.content['args']
		kwargs = launchevent.content['kwargs']

		## thread or process
		if newproc:
			self.caller.launchCall('fork',targetclass,args,kwargs)
		else:
			self.caller.launchCall('thread',targetclass,args,kwargs)

	def launchThread(self):
		pass

	def launchProcess(self):
		pass

#	def launchNode(self, nodeid, nodeclass, args = None):
#		## new node's manager = launcher's manager
#		print 'launching %s %s' % (nodeid, nodeclass)
#		nodeargs = tuple([nodeid, self.managerloc] + list(args))
#		apply(nodeclass, nodeargs)
#
#	def launchDataServer(self, dataserverclass):
#		print 'launching %s' % nodeclass
#		dataserverclass()


if __name__ == '__main__':
	import sys,socket

	manloc = {}
	manloc['hostname'] = sys.argv[1]
	manloc['TCP port'] = int(sys.argv[2])

	myhost = socket.gethostname()

	m = Launcher(myhost, manloc)
