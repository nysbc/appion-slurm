#!/usr/bin/env python
# client/server model in which client requests data from the server

import leginonobject
import datalocal
import datatcp
import threading

class Client(leginonobject.LeginonObject):
  # hostname/port -> location or whatever
	def __init__(self, hostname, port):
		leginonobject.LeginonObject.__init__(self)
		self.clients = {}
		self.clients[datalocal.PullClient] = datalocal.PullClient()
		self.clients[datatcp.PullClient] = datatcp.PullClient(hostname, port)

	def pull(self, dataid):
		# testing, needs to be smart
		return self.clients[datatcp.PullClient].pull(dataid)

class Server(leginonobject.LeginonObject):
	def __init__(self):
		leginonobject.LeginonObject.__init__(self)
		self.servers = {}
		self.servers[datalocal.PullServer] = datalocal.PullServer(self)
		self.servers[datatcp.PullServer] = datatcp.PullServer(self)
		thread = threading.Thread(None, self.servers[datatcp.PullServer].serve_forever, None, (), {})
		# this isn't working right now
		#thread.setDaemon(1)
		thread.start()

if __name__ == '__main__':
	class MyServer(Server):
		def __init__(self):
			Server.__init__(self)
			self.data = {'0' : 'foo', '1' : 'bar'}
		def datafromid(self, data_id):
			try:
				return self.data[data_id]
			except KeyError:
				return None

	foo = MyServer()
	print foo.servers[datatcp.PullServer].server_address

