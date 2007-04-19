# COPYRIGHT:
# The Leginon software is Copyright 2003
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
 
import data
import dbdatakeeper

db=dbdatakeeper.DBDataKeeper(db='dbparticledata')

]class ApMaskRegionData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('mask', makeMaskParams),
			('imageId', image),
			('x', int),
			('y', int),
			('area', int),
			('perimeter', int),
			('mean', float),
			('stdev', float),
			('keep', bool),
			
		)
	typemap = classmethod(typemap)
data.ApMaskRegionData=ApMaskRegionData

class ApParticleData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('runId', run),
			('imageId', image),
			('selectionId', selectionParams),
			('xcoord', int),
			('ycoord', int),
			('correlation', float),
			('insidecrud', int),
		)
	typemap = classmethod(typemap)
data.ApParticleData=ApParticleData

class ApSelectionRunData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('dbemdata|SessionData|session', int),
			('name', str), 
		)
	typemap = classmethod(typemap)
data.ApSelectionRunData=ApSelectionRunData

class ApSelectionParamsData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('runId', run),
			('diam', int),
			('bin', int),
			('manual_thresh', float),
			('auto_thresh', int),
			('lp_filt', int),
			('hp_filt', int),
			('crud_diameter', int),
			('crud_blur', float),
			('crud_low', float),
			('crud_high', float),
			('crud_std', float),
		)
	typemap = classmethod(typemap)
data.ApSelectionParamsData=ApSelectionParamsData

class ApShiftData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('dbemdata|AcquisitionImageData|image1', int),
			('dbemdata|AcquisitionImageData|image2', int),
			('shiftx', float),
			('shifty', float),
			('correlation', float),
			('scale', float),
		)
	typemap = classmethod(typemap)
data.ApShiftData=ApShiftData

class ApTemplateImageData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('project|projects|projectId', int),
			('templatepath', str),
			('apix', float),
			('diam', int),
			('description', str),
		)
	typemap = classmethod(typemap)
data.ApTemplateImageData=ApTemplateImageData

class ApTemplateRunData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('templateId', templateImage),
			('runId', run),
			('range_start', int),
			('range_end', int),
			('range_incr', int),
		)
	typemap = classmethod(typemap)
data.ApTemplateRunData=ApTemplateRunData

class ApMakeMaskParamsData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('dbemdata|SessionData|session', int),
			('mask path', str),
			('name', str),
			('bin', int),
			('mask type', str),
			('pdiam', int),
			('region diameter', int),
			('edge blur', float),
			('edge low', float),
			('edge high', float),
			('region std', float),
			('convolve', float),
			('convex hull', bool),
			('libcv', bool),
		)
	typemap = classmethod(typemap)
data.ApMakeMaskParamsData=ApMakeMaskParamsData

class ApStackParamsData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('stackPath', str),
			('name' , str),
			('description', str),
			('boxSize', int),
			('bin', int),
			('phaseFlipped', bool),
			('aceCutoff', float),
			('selexonCutoff', float),
			('checkCrud', bool),
			('checkImage', bool),
			('minDefocus', float),
			('maxDefocus', float),
			('fileType', str),
			('inverted', bool),
		)
	typemap = classmethod(typemap)
data.ApStackParamsData=ApStackParamsData

class ApMaskMakerSettingsData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('dbemdata|SessionData|session', int),
			('mask path', str),
			('name', str),
			('bin', int),
			('mask type', str),
			('pdiam', int),
			('region diameter', int),
			('edge blur', float),
			('edge low', float),
			('edge high', float),
			('region std', float),
			('convolve', float),
			('convex hull', bool),
			('libcv', bool),
		)
	typemap = classmethod(typemap)
data.ApMaskMakerSettingsData=ApMaskMakerSettingsData

class ApStackParticlesData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('particleNumber', int),
			('stackId', stackParams),
			('particleId', particle),
	        )
	typemap = classmethod(typemap)
data.ApStackParticlesData = ApStackParticlesData

### Reconstruction Tables ###

class ApReconRunData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('name', str),
			('stackId', stackParams),
			('initialModelId', initialModel),
			('path', str),
			('package', str),
		)
	typemap = classmethod(typemap)
data.ApReconRunData=ApReconRunData

class ApInitialModelData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('path', str),
			('name', str),
			('symmetryId', symmetry),
			('pixelsize', float),
			('boxsize', int),
			('description', str),
		)
	typemap = classmethod(typemap)
data.ApInitialModelData=ApInitialModelData

class ApSymmetryData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('symmetry', str),
			('description', str),
		)
	typemap = classmethod(typemap)
data.ApSymmetryData=ApSymmetryData

class ApRefinementData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('reconRunId', reconRun),
			('refinementParamsId', refinementParams),
			('iteration', int),
			('resolutionId', resolution),
			('classAverage', str),
			('classVariance', str),
			('numClassAvg', int),
			('numClassAvgKept', int),
			('numBadParticles', int),
			('volumeSnapshot', str),
			('volumeDensity',str),
		)
	typemap = classmethod(typemap)
data.ApRefinementData=ApRefinementData

class ApRefinementParamsData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('angIncr', float),
			('mask', int),
			('imask', int),
			('lpfilter', int),
			('hpfilter', int),
			('fourier_padding', int),
			('EMAN_hard', int),
			('EMAN_classkeep', float),
			('EMAN_classiter', int),
			('EMAN_median', bool),
			('EMAN_phasecls', bool),
			('EMAN_refine', bool),
		)
	typemap = classmethod(typemap)
data.ApRefinementParamsData=ApRefinementParamsData

class ApResolutionData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('fscfile', str),
			('half', float),
		)
	typemap = classmethod(typemap)
data.ApResolutionData=ApResolutionData

class ApParticleClassificationData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('refinementId', refinement),
			('particleId', particle),
			('classnumber', int),
			('euler1', float),
			('euler2', float),
			('euler3', float),
			('shiftx', float),
			('shifty', float),
			('inplane_rotation', float),
			('quality_factor', float),
			('thrown_out',int),
		)
	typemap = classmethod(typemap)
data.ApParticleClassificationData=ApParticleClassificationData

class ApAceRunData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('dbemdata|SessionData|session', int),
			('name', str), 
		)
	typemap = classmethod(typemap)
data.ApAceRunData=ApAceRunData

class ApAceParamsData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('runId', run),
			('display', int), 
			('stig', int),
			('medium', str),
			('df_override', float),
			('edgethcarbon', float),
			('edgethice', float),
			('pfcarbon', float),
			('pfice', float),
			('overlap', int),
			('fieldsize', int),
			('resamplefr', float),
			('drange', int),
			('reprocess', float),
		)
	typemap = classmethod(typemap)
data.ApAceParamsData=ApAceParamsData

class ApCtfData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('runId', run),
			('aceId', ace_params),
			('imageId', image),
			('defocus1', float),
			('defocus2', float), 
			('defocusinit', float), 
			('amplitude_contrast', float), 
			('angle_astigmatism', float), 
			('noise1', float), 
			('noise2', float), 
			('noise3', float), 
			('noise4', float), 
			('envelope1', float), 
			('envelope2', float), 
			('envelope3', float), 
			('envelope4', float), 
			('lowercutoff', float), 
			('uppercutoff', float), 
			('snr', float), 
			('confidence', float), 
			('confidence_d', float), 
			('graph1', str),
			('graph2', str),
			('mat_file', str),
		)
	typemap = classmethod(typemap)
data.ApCtfData=ApCtfData

class ApCtfBlobData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('ctfId', ctf),
			('imageId', image),
			('blobgraph1', float),
			('blobgraph2', float),
		)
	typemap = classmethod(typemap)
data.ApCtfBlobData=ApCtfBlobData

