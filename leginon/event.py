#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

## defines the Event and EventHandler classes

import leginonobject
import data

### False is not defined in early python 2.2
False = 0
True = 1

def eventClasses():
	"""
	returns a dict:   {name: class_object, ...}
	that contains all the Event subclasses defined in this module
	"""
	eventclasses = {}
	all_attrs = globals()
	for name,value in all_attrs.items():
		if type(value) == type:
			if issubclass(value, Event):
				eventclasses[name] = value
	return eventclasses

class Event(data.Data):
	def typemap(cls):
		t = data.Data.typemap()
		t += [ ('confirm', int), ]
		return t
	typemap = classmethod(typemap)

class EventLog(data.Data):
	def typemap(cls):
		t = data.Data.typemap()
		t += [ ('eventclass', str), ('status', str), ]
		return t
	typemap = classmethod(typemap)


## Standard Event Types:
##
##	Event
##		NotificationEvent
##			NodeAvailableEvent
##				LauncherAvailableEvent
##			NodeUnavailableEvent
##			PublishEvent
##			UnpublishEvent
##			ListPublishEvent
##			ConfirmationEvent
##		ControlEvent
##			StartEvent
##			Stopvent
##			KillEvent
##			PauseEvent
##			ResumeEvent
##			NumericControlEvent
##			LaunchEvent
##			LockEvent
##			UnlockEvent

### generated by a node to notify manager that node is ready
class NotificationEvent(Event):
	'Event sent for notification'
	pass

## I'm definietely not sure about this one
class NodeAvailableEvent(NotificationEvent):
	'Event sent by a node to the manager to indicate that it is accessible'
	def typemap(cls):
		t = NotificationEvent.typemap()
		t += [ ('location', dict), ('nodeclass', str), ]
		return t
	typemap = classmethod(typemap)

class NodeUnavailableEvent(NotificationEvent):
	'Event sent by a node to the manager to indicate that it is inaccessible'
	pass

class NodeInitializedEvent(NotificationEvent):
	'Event sent by a node to indicate that it is operational'
	pass

class NodeUninitializedEvent(NotificationEvent):
	'Event sent by a node to indicate that it is no longer operational'
	pass

class TargetListDoneEvent(NotificationEvent):
	'Event indicating target list is done'
	def typemap(cls):
		t = NotificationEvent.typemap()
		t += [ ('targetlistid', tuple), ('status', str)]
		return t
	typemap = classmethod(typemap)

class ImageProcessDoneEvent(NotificationEvent):
	'Event indicating target list is done'
	def typemap(cls):
		t = NotificationEvent.typemap()
		t += [ ('imageid', tuple), ('status', str)]
		return t
	typemap = classmethod(typemap)

class DriftDoneEvent(NotificationEvent):
	'Event indicating that drift has ended'
	def typemap(cls):
		t = NotificationEvent.typemap()
		t += [('status', str)]
		return t
	typemap = classmethod(typemap)

class GridInsertedEvent(NotificationEvent):
	'Event indicating a grid has been inserted'
	def typemap(cls):
		t = NotificationEvent.typemap()
		t += [('grid number', int)]
		return t
	typemap = classmethod(typemap)

class GridExtractedEvent(NotificationEvent):
	'Event indicating a grid has been extracted'
	def typemap(cls):
		t = NotificationEvent.typemap()
		t += [('grid number', int)]
		return t
	typemap = classmethod(typemap)

class MosaicDoneEvent(NotificationEvent):
	'Event indicating mosaic is done'
	pass

## could PublishEvent and UnpublishEvent be derived from a common class?
class PublishEvent(NotificationEvent):
	'Event indicating data was published'
	dataclass = data.Data
	def typemap(cls):
		t = NotificationEvent.typemap()
		t += [ ('dataid', tuple), ]
		return t
	typemap = classmethod(typemap)

class UnpublishEvent(NotificationEvent):
	'Event indicating data was unpublished (deleted)'
	def typemap(cls):
		t = NotificationEvent.typemap()
		t += [ ('dataid', tuple), ]
		return t
	typemap = classmethod(typemap)

class ConfirmationEvent(NotificationEvent):
	'Event sent to confirm event processing'
	def typemap(cls):
		t = NotificationEvent.typemap()
		t += [ ('eventid', tuple), ]
		return t
	typemap = classmethod(typemap)

# this could be a subclass of publish event, but I'm not sure if that
# would confuse those not looking for a list
class ListPublishEvent(Event):
	'Event indicating data was published'
	def typemap(cls):
		t = Event.typemap()
		t += [ ('idlist', list), ]
		return t
	typemap = classmethod(typemap)

class ImageTargetShiftPublishEvent(PublishEvent):
	dataclass = data.ImageTargetShiftData

class NeedTargetShiftEvent(NotificationEvent):
	'''notify DriftManager that I want another ImageTargetShift'''
	def typemap(cls):
		t = NotificationEvent.typemap()
		t += [ ('imageid', tuple), ]
		return t
	typemap = classmethod(typemap)

## this is a PublishEvent because we want to publish the EM state
## that was used to detect the drift, so that we can continue to monitor
## drift at this state.
class DriftDetectedEvent(PublishEvent):
	dataclass = data.AllEMData
	
class NodeClassesPublishEvent(PublishEvent):
	'Event indicating launcher published new list of node classes'
	dataclass = data.NodeClassesData

class ImagePublishEvent(PublishEvent):
	'Event indicating image was published'
	dataclass = data.ImageData

class CameraImagePublishEvent(ImagePublishEvent):
	'Event indicating camera image was published'
	dataclass = data.CameraImageData

class PresetImagePublishEvent(CameraImagePublishEvent):
	'Event indicating preset camera image was published'
	dataclass = data.PresetImageData

class AcquisitionImagePublishEvent(PresetImagePublishEvent):
	dataclass = data.AcquisitionImageData

class TrialImagePublishEvent(PresetImagePublishEvent):
	dataclass = data.TrialImageData

class CorrectorImagePublishEvent(CameraImagePublishEvent):
	dataclass = data.CorrectorImageData

class MosaicPublishEvent(PublishEvent):
	'Event indicating mosaic image was published'
	dataclass = data.MosaicData

class DarkImagePublishEvent(CorrectorImagePublishEvent):
	dataclass = data.DarkImageData

class BrightImagePublishEvent(CorrectorImagePublishEvent):
	dataclass = data.BrightImageData

class NormImagePublishEvent(CorrectorImagePublishEvent):
	dataclass = data.NormImageData

class CorrelationImagePublishEvent(ImagePublishEvent):
	dataclass = data.NormImageData

class CrossCorrelationImagePublishEvent(CorrelationImagePublishEvent):
	dataclass = data.CrossCorrelationImageData

class PhaseCorrelationImagePublishEvent(CorrelationImagePublishEvent):
	dataclass = data.PhaseCorrelationImageData

class ImageTargetListPublishEvent(PublishEvent):
	dataclass = data.ImageTargetListData

class ControlEvent(Event):
	'Event that passes a value with it'
	pass

class KillEvent(ControlEvent):
	'Event that signals a kill'
	pass

class LaunchEvent(ControlEvent):
	'ControlEvent sent to a NodeLauncher specifying a node to launch'
	def typemap(cls):
		t = ControlEvent.typemap()
		t += [
			('newproc', int),
			('targetclass', str),
			('args', tuple),
			('kwargs', dict)
		]
		return t
	typemap = classmethod(typemap)

class LockEvent(ControlEvent):
	'Event that signals a lock'
	pass
	
class UnlockEvent(ControlEvent):
	'Event that signals an unlock'
	pass

class InsertGridEvent(ControlEvent):
	'Event that signals a grid to be inserted'
	def typemap(cls):
		t = NotificationEvent.typemap()
		t += [('grid number', int)]
		return t
	typemap = classmethod(typemap)

class ExtractGridEvent(ControlEvent):
	'Event that signals a grid to be extracted'
	pass

class PublishSpiralEvent(ControlEvent):
	'Event telling sprial target maker to publish a spiral '
	pass

## this is basically the same as data.ImageTargetData
class ImageClickEvent(Event):
	def typemap(cls):
		t = Event.typemap()
		t += [
		  ('canvas x', int),
		  ('canvas y', int),
		  ('image x', int),
		  ('image y', int),
		  ('array shape', tuple),
		  ('array row', int),
		  ('array column', int),
		  ('array value', float),

		  ('image', data.ImageData),
		  ('scope', dict),
		  ('camera', dict),
		  ('source', str),
		  ('preset', data.PresetData)
		]
		return t
	typemap = classmethod(typemap)

class ImageAcquireEvent(Event):
	pass

class ChangePresetEvent(Event):
	def typemap(cls):
		t = Event.typemap()
		t += [ ('name', str), ('emtarget', data.EMTargetData)]
		return t
	typemap = classmethod(typemap)

class PresetChangedEvent(Event):
	def typemap(cls):
		t = Event.typemap()
		t += [ ('name', str), ]
		return t
	typemap = classmethod(typemap)

##############################################################
## generate the mapping of data class to publish event class
publish_events = {}
event_classes = eventClasses()
for eventclass in event_classes.values():
	if issubclass(eventclass, PublishEvent):
		if hasattr(eventclass, 'dataclass'):
			publish_events[eventclass.dataclass] = eventclass


###########################################################
###########################################################
## event related exceptions

class InvalidEventError(TypeError):
	pass

