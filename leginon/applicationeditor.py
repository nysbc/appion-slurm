import Tkinter
import math
import application

class Line(object):
	def __init__(self, canvas, position1, position2):
		self.canvas = canvas
		self.createline(position1, position2)

	def createline(self, position1, position2):
		self.line = self.canvas.create_line(position1[0], position1[1],
																				position2[0], position2[1])

	def move(self, position1, position2):
		self.canvas.coords(self.line, position1[0], position1[1],
																	position2[0], position2[1])

	def delete(self):
		self.canvas.delete(self.line)

class ArrowLine(Line):
	def __init__(self, canvas, originposition, destinationpostion,
																								destination=None):
		self.canvas = canvas
		self.destination = destination
		self.createline(originposition, destinationpostion)

	def createline(self, originposition, destinationposition):
		Line.createline(self, originposition, destinationposition)
		self.createArrow(originposition, destinationposition)

	def move(self, originposition, destinationposition, destination=None):
		Line.move(self, originposition, destinationposition)
		self.moveArrow(originposition, destinationposition, destination)

	def createArrow(self, originposition, destinationposition):
		c = self.arrowCoordinates(originposition, destinationposition)
		self.arrow = self.canvas.create_polygon(c[0], c[1], c[2], c[3], c[4], c[5])

	def moveArrow(self, originposition, destinationposition, destination=None):
		c = self.arrowCoordinates(originposition, destinationposition, destination)
		self.canvas.coords(self.arrow, c[0], c[1], c[2], c[3], c[4], c[5])

	def arrowCoordinates(self, originposition, destinationposition,
																									destination=None):
		side = 10

		if destination is not None:
			head = self.lineNodeLabelIntersect(originposition, destinationposition,
																																	destination)
			if head is None:
				head = destinationposition
		elif self.destination is not None:
			head = self.lineNodeLabelIntersect(originposition, destinationposition,
																														self.destination)
			if head is None:
				head = destinationposition
		else:
			head = destinationposition
		angle = math.atan2(float(destinationposition[1] - originposition[1]),
								float(destinationposition[0] - originposition[0])) + math.pi

		x0 = head[0]
		y0 = head[1]

		newangle = angle + math.pi/6
		x1 = x0 + math.cos(newangle)*side
		y1 = y0 + math.sin(newangle)*side

		newangle = angle - math.pi/6
		x2 = x0 + math.cos(newangle)*side
		y2 = y0 + math.sin(newangle)*side

		return (x0, y0, x1, y1, x2, y2)

	def delete(self):
		Line.delete(self)
		self.canvas.delete(self.arrow)

	def samesigns(self, a, b):
		if (a < 0 and b < 0) or (a >= 0 and b >= 0):
			return True
		else:
			return False

	def lineIntersect(self, line1, line2):
		x1 = line1[0]
		y1 = line1[1]
		x2 = line1[2]
		y2 = line1[3]

		x3 = line2[0]
		y3 = line2[1]
		x4 = line2[2]
		y4 = line2[3]

		a1 = y2 - y1
		b1 = x1 - x2
		c1 = x2 * y1 - x1 * y2

		r3 = a1 * x3 + b1 * y3 + c1
		r4 = a1 * x4 + b1 * y4 + c1

		if r3 != 0 and r4 != 0 and self.samesigns(r3, r4):
			return None

		a2 = y4 - y3
		b2 = x3 - x4
		c2 = x4 * y3 - x3 * y4

		r1 = a2 * x1 + b2 * y1 + c2
		r2 = a2 * x2 + b2 * y2 + c2

		if r1 != 0 and r2 != 0 and self.samesigns(r1, r2):
			return None

		denom = a1 * b2 - a2 * b1
		if denom == 0:
			# colinear
			return None
		if denom < 0:
			offset = -denom/2
		else:
			offset = denom/2

		num = b1 * c2 - b2 * c1
		if num < 0:
			x = (num - offset)/ denom
		else:
			x = (num + offset)/ denom

		num = a2 * c1 - a1 * c2
		if num < 0:
			y = (num - offset)/ denom
		else:
			y = (num + offset)/ denom

		return (x, y)

	def lineBoxIntersect(self, line, box):
		boxlines = [(box[0], box[1], box[2], box[1]),
								(box[2], box[1], box[2], box[3]),
								(box[2], box[3], box[0], box[3]),
								(box[0], box[3], box[0], box[1])]

		for boxline in boxlines:
			result = self.lineIntersect(line, boxline)
			if result is not None:
				return result

		return None

	def lineNodeLabelIntersect(self, position1, position2, widget):
		return self.lineBoxIntersect((position1[0], position1[1],
														position2[0], position2[1]),
														widget.getBox())

class LabeledLine(ArrowLine):
	def __init__(self, canvas, originposition, destinationposition, destination, text):
		self.text = text
		ArrowLine.__init__(self, canvas, originposition, destinationposition, destination)

	def createline(self, originposition, destinationposition):
		ArrowLine.createline(self, originposition, destinationposition)

		self.labeltext = Tkinter.StringVar()
		self.labeltext.set(self.text)
		self.label = Tkinter.Label(self.canvas, textvariable=self.labeltext,
																relief=Tkinter.RAISED, justify=Tkinter.LEFT,
																bd=1, padx=5, pady=3, bg='white')
		self.label.lower()
		self.label.place(
							x = (int(destinationposition[0]) + int(originposition[0]))/2,
							y = (int(destinationposition[1]) + int(originposition[1]))/2,
							anchor=Tkinter.CENTER)

	def move(self, originposition, destinationposition, destination=None):
		ArrowLine.move(self, originposition, destinationposition, destination)
		self.label.place(
							x = (int(destinationposition[0]) + int(originposition[0]))/2,
							y = (int(destinationposition[1]) + int(originposition[1]))/2,
							anchor=Tkinter.CENTER)

	def delete(self):
		ArrowLine.delete(self)
		self.label.place_forget()

	def append(self, itext):
		otext = self.labeltext.get()
		self.labeltext.set(otext + '\n' + itext)

class ConnectionManager(Line):
	def __init__(self, canvas):
		self.canvas = canvas
		self.activeconnection = None
		self.lines = {}

	def setActiveConnectionPosition(self, destination):
		if self.activeconnection is not None:
			originposition = self.activeconnection['origin'].getPosition()
			destinationposition = destination.getPosition()
			self.activeconnection['line'].move(originposition, destinationposition,
																																	destination)

	def setActiveConnectionPositionRaw(self, position):
		originposition = self.activeconnection['origin'].getPosition()
		self.activeconnection['line'].move(originposition, position)

	def offsetPosition(self, origin, destination):
		originposition = origin.getPosition()
		destinationposition = destination.getPosition()
		if self.lines[(origin, destination)]['offset']:
			offset = 10
			angle = math.atan2(float(destinationposition[1] - originposition[1]),
												float(destinationposition[0] - originposition[0]))
			newangle = math.pi/2 + angle
			offsetvector = (math.cos(newangle)*offset, math.sin(newangle)*offset)
			line = ((originposition[0] + offsetvector[0],
								originposition[1] + offsetvector[1]),
							(destinationposition[0] + offsetvector[0],
								destinationposition[1] + offsetvector[1]))
		else:
			line = ((originposition[0], originposition[1]),
							(destinationposition[0], destinationposition[1]))
		return line

	def addConnection(self, origin, destination, text):
		# could send events to self, not bothering for now
		if origin == destination:
			return
		key = (origin, destination)
		if key in self.lines:
			self.lines[key]['line'].append(text)
		else:
			self.lines[key] = {}
			inversekey = (destination, origin)
			if inversekey in self.lines:
				self.lines[key]['offset'] = True
				self.lines[inversekey]['offset'] = True
				position = self.offsetPosition(destination, origin)
				self.lines[inversekey]['line'].move(position[0], position[1])
			else:
				self.lines[key]['offset'] = False

			position = self.offsetPosition(origin, destination)
			self.lines[key]['line'] = LabeledLine(self.canvas, position[0],
																						position[1], destination, text)

	def refreshConnections(self, widget):
		for key in self.lines:
			if key[0] == widget or key[1] == widget:
				position = self.offsetPosition(key[0], key[1])
				self.lines[key]['line'].move(position[0], position[1])

	def startConnection(self, origin, text='<None>'):
		if self.activeconnection is None:
			position = origin.getPosition()
			self.activeconnection = {}
			self.activeconnection['origin'] = origin
			self.activeconnection['text'] = text
			self.activeconnection['line'] = LabeledLine(self.canvas, position,
																									position, None, text)

	def finishConnection(self, destination):
		if self.activeconnection is not None:
			self.activeconnection['line'].delete()
			self.addConnection(self.activeconnection['origin'], destination,
																					self.activeconnection['text'])
			self.activeconnection = None

	def abortConnection(self, ievent=None):
		if self.activeconnection is not None:
			self.activeconnection['line'].delete()
			self.activeconnection = None

class NodeLabel(object):
	def __init__(self, canvas, itext, editor):
		self.canvas = canvas
		self.label = Tkinter.Label(self.canvas, text=itext, relief=Tkinter.RAISED,
												justify=Tkinter.LEFT, bd=1, padx=5, pady=3, bg='white')
		self.editor = editor
		self.label.bind('<Button-3>', self.editor.connectionmanager.abortConnection)
		self.label.bind('<Motion>', self.moveConnection)
		self.label.bind('<B1-Motion>', self.drag)
		self.label.bind('<Button-1>', self.startDrag)
		self.label.bind('<Double-Button-1>', self.handleConnection)

	def getBox(self):
		height = self.label.winfo_reqheight()
		width = self.label.winfo_reqwidth()
		position = self.getPosition()
		return ((position[0]*2 - width)/2, (position[1]*2 - height)/2,
						(position[0]*2 + width)/2, (position[1]*2 + height)/2)

	def getPosition(self):
		info = self.label.place_info()
		return (int(info['x']), int(info['y']))

	def move(self, x0, y0):
		self.label.place(x = x0, y = y0, anchor=Tkinter.CENTER)
		self.editor.connectionmanager.refreshConnections(self)

	def moveConnection(self, ievent):
		if self.editor.connectionmanager.activeconnection is not None:
			self.editor.connectionmanager.setActiveConnectionPosition(self)

	def drag(self, ievent):
		self.editor.connectionmanager.abortConnection()
		position = self.getPosition()
		self.move(position[0] + ievent.x - self.dragoffset[0],
							position[1] + ievent.y - self.dragoffset[1])

	def startDrag(self, ievent):
		self.dragoffset = (ievent.x, ievent.y)

	def handleConnection(self, ievent):
		if self.editor.connectionmanager.activeconnection is None:
			self.editor.connectionmanager.startConnection(self)
		else:
			self.editor.connectionmanager.finishConnection(self)

class Editor(Tkinter.Frame):
	def __init__(self, parent, **kwargs):
		Tkinter.Frame.__init__(self, parent, **kwargs)
		self.pack(fill=Tkinter.BOTH, expand=1)
		self.nodes = []
		self.canvas = Tkinter.Canvas(self, height=600, width=800, bg='white')
		self.connectionmanager = ConnectionManager(self.canvas)
		self.canvas.bind('<Button-3>', self.connectionmanager.abortConnection)
		self.canvas.bind('<Motion>', self.moveConnection)
		self.canvas.pack(fill=Tkinter.BOTH, expand=1)

	def moveConnection(self, ievent):
		if self.connectionmanager.activeconnection is not None:
			self.connectionmanager.setActiveConnectionPositionRaw((ievent.x,ievent.y))

	def addNode(self, text):
		node = NodeLabel(self.canvas, text, self)
		self.nodes.append(node)
		self.circle()
		return node

	def circle(self):
		radius = (250, 200)
		center = (400, 300)
		angle = 2*math.pi/len(self.nodes)
		for i in range(len(self.nodes)):
			self.nodes[i].move(int(round(math.cos(i*angle)*radius[0] + center[0])),
													int(round(math.sin(i*angle)*radius[1] + center[1])))

class ApplicationEditor(Editor):
	def __init__(self, parent, **kwargs):
		Editor.__init__(self, parent, **kwargs)
		self.mapping = {}

	def load(self, filename):
		self.app = application.Application(('AE Application',), None)
		self.app.load(filename)
		for args in self.app.launchspec:
			self.displayNode(args)
		for binding in self.app.bindspec:
			self.displayConnection(binding)

	def displayNode(self, args):
		labelstring = \
					"Name: %s\nClass: %s\nLauncher: %s\nProcess: %s\nArgs: %s" \
														% (args[3], args[2], args[0], args[1], args[4])
		self.mapping[('manager', args[3])] = Editor.addNode(self, labelstring)

	def displayConnection(self, binding):
		self.connectionmanager.addConnection(self.mapping[binding[1]],
																					self.mapping[binding[2]],
																					str(binding[0]))

if __name__ == '__main__':
	import sys

	root = Tkinter.Tk()
	ae = ApplicationEditor(root)
	ae.load(sys.argv[1])
	ae.pack()
	root.mainloop()

