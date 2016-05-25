<?php

/**
 *	The Leginon software is Copyright 2003
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "basicLayoutForm.inc"; //includes the BasicLayoutForm class that this class extends
require_once "inc/particledata.inc"; // needed to look up symmetry values

class RelionAlign2DForm extends BasicLayoutForm
{
	protected $stackIds;

	// Set Default values in the constructor
	function __construct( $expId, $extraHTML='', $stackId='', $clip='', $bin='1', $numpart='3000',
		$lowpass='10', $highpass='1000', $numRef='3', $maxIter='30', $angStep='5', $tau='2', $partDiam='',
		$flat='on', $mpinodes='2',$mpiprocs='4',$mpithreads='1',$mpimem='4', $commit='on')
	{
		parent::__construct($expId, $extraHTML);

		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//

		// Set the publications to be references on the web pages
		$pubList = array('relion'); // Keys are found in publicationList.inc
		$this->setPublications( $pubList ); // list of references to display

		$this->setJobType( 'partalign' ); //Job type stored in database
		$this->setOutputDirectory( 'align' ); // the general folder this job run will be stored in, along with others of this type
		$this->setBaseRunName( 'rmaxlike' ); // a unique number will be added to this to create the run name
		$this->setTitle( 'Relion 2D Maximum Likelihood Alignment Launcher' ); // Shows up in the browser tab
		$this->setHeading( 'Relion 2D Maximum Likelihood Alignment' ); // shows at the top of the processing page
		$this->setExeFile( 'relionMaxlikeAlignment.py' ); // added to the command string
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Relion_2D_Alignment" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( True ); // Flag to hide the description field of the run parameters.
		$this->setUseCluster( True ); // Shows the processing host params to set processors and memory

		//------ Add JavaScript functions needed for this form -------------------------//

		$javascript = "<script src='../js/viewer.js'></script>\n";
		// javascript to switch the defaults based on the stack
		$javascript .= "<script>\n";
		$javascript .= "function switchDefaults(stackval) {\n";
		$javascript .= "	var stackArray = stackval.split('|--|');\n";
		// remove commas from number : list($stackid, $apix, $boxsz, $totpart)
		$javascript .= "	stackArray[3] = stackArray[3].replace(/\,/g,'');\n";
		$javascript .= "	document.viewerform.numpart.value = stackArray[3];\n";
		$javascript .= "	document.viewerform.clip.value = stackArray[2];\n";
		$javascript .= "	document.viewerform.numRef.value = Math.ceil(Math.sqrt(stackArray[3])/10+1);\n";
		$javascript .= "	document.viewerform.partDiam.value = Math.floor(document.viewerform.clip.value*2/6)*2;\n";

		// set binning
		$javascript .= "	var bestbin = Math.floor(stackArray[2]/80);\n";
		$javascript .= "	if (bestbin < 1) {\n";
		$javascript .= "		var bestbin = 1 ;}\n";
		$javascript .= "	document.viewerform.bin.value = bestbin;\n";
		// set particle & mask radius and lp
		$javascript .= "}\n";
		$javascript .= "</script>\n";

		$this->addJavaScript( $javascript );

		//------ Set Parameters specific to the program that requires this new form -----//

		$particle = new particledata();
		$this->stackIds = $particle->getStackIds($expId);

		$params = $this->getFormParams();

		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "appion" );

		// Add each of the parameters here.
		// addParam( "key", default_value, "Label that appears in GUI")

		$params->addParam( "mpinodes", $mpinodes, "Number of nodes allocated for entire job." );
		$params->addParam( "mpiprocs", $mpiprocs, "Number of processors allocated for a subjob. For memory intensive jobs, decrease this value." );
		$params->addParam( "mpithreads", $mpithreads, "Number of threads to generate per processor. For memory intensive jobs, increase this value." );

		$params->addParam( "mpimem", $mpimem, "Amount of memory (Gb) to allocate per thread. Increase this value for memory intensive jobs." );

		$params->addParam( "stack", $stackId, "Select a stack of particles to use" );
		$params->addParam( "clip", $clip, "Unbinned Clip Diameter" );
		$params->addParam( "bin", $bin, "Particle Binning" );
		$params->addParam( "numpart", $numpart, "Number of Particles" );
		$params->addParam( "lowpass", $lowpass, "Low Pass Filter Radius" );
		$params->addParam( "highpass", $highpass, "High Pass Filter Radius" );
		$params->addParam( "partDiam", $partDiam, "Particle Diameter" );
		$params->addParam( "numRef", $numRef, "Number of References" );
		$params->addParam( "maxIter", $maxIter, "Maximum Number of Iterations" );
		$params->addParam( "angStep", $angStep, "In-plane Rotation Angle Interval" );
		$params->addParam( "tau", $tau, "Regularisation parameter" );
		$params->addParam( "flat", $flat, "Flatten Solvent on References " );

		$params->addParam( "commit", $commit, "Commit to Database" );

		// Validations
		$params->addValidation( "numpart", "minval=4" );

	}

	// Generate a form for the parameters that are specific to this program
	// The Left side will just show the stack and model that the user selected
	// on the previous pages. This overrides the generateAdditionalFormLeft()
	// function that is found in the BasicLayoutForm class.
	public function generateAdditionalFormRight()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();

		$fieldSize = 5;


  $html .= "
            <br />
            <H4>MPI Configuration</H4>
            <hr />";
		$html.= "<br />";
		$html.= $params->insertTextField( "mpinodes", $fieldSize, '', 'appion.mpinodes' );
                $html.= $params->insertTextField( "mpiprocs", $fieldSize, '', 'appion.mpiprocs' );
                $html.= $params->insertTextField( "mpithreads", $fieldSize, '', 'appion.mpithreads' );

		$html.= $params->insertTextField( "mpimem", $fieldSize, '', 'appion.mpimem' );


		$html .= "
	    <br />
	    <H4>Data limiting numbers</H4>
	    <hr />";

		$html.= $params->insertTextField( "clip", $fieldSize, "(pixels)", 'appion.clipdiam' );
		$html.= $params->insertTextField( "bin", $fieldSize, '', 'appion.partbin' );
		$html.= $params->insertTextField( "numpart", $fieldSize, '', 'appion.numpart' );

		$html .= "
	    <br />
	    <H4>Filters</H4>
	    <hr />";

		$html.= $params->insertTextField( "lowpass", $fieldSize, "(&Aring;ngstroms)",'appion.lpstackval' );
		$html.= $params->insertTextField( "highpass", $fieldSize, "(&Aring;ngstroms)", 'appion.hpstackval' );

		$html .= "
	    <br />
	    <H4>Alignment Parameters</H4>
	    <hr />";

		$html.= $params->insertTextField( "partDiam", $fieldSize,"(&Aring;ngstroms)",'appion.diameter' );
		$html.= $params->insertTextField( "numRef", $fieldSize,'','appion.numref' );
		$html.= $params->insertTextField( "maxIter", $fieldSize,'','appion.maxiter' );
		$html.= $params->insertTextField( "angStep", $fieldSize,'(degrees)','appion.angleinc' );
		$html.= $params->insertTextField( "tau", $fieldSize,'','appion.tau2fudge' );
		$html.= $params->insertCheckboxField("flat");


		// When loading this page the first time, use the switchDefaults javascript function to set
		// form parameters based on the currently selected stack.
		if (!$_POST['process']) {
			$html.= "<script>switchDefaults(document.viewerform.stack.options[document.viewerform.stack.selectedIndex].value);</script>\n";
		}

		return $html;
	}

	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();

		if (!$this->stackIds) {
			$html =  "<font color='red'><B>No Stacks for this Session</B></FONT>\n";
		} else {
			$onchange 	= "switchDefaults(this.value)";
			$particle 	= new particledata();
			$options 	= $particle->getStackOptions($this->stackIds);
			$html 		= $params->insertStackedSelectField( "stack", $options,'', '', $onchange );
		}

		$html .= "<br />";
		$html .= $params->insertCheckboxField("commit");

		return $html;
	}

	// Override the buildCommand function to adapt to the old python command
	// that uses "-" in params and parse the stack id.
	public function buildCommand( $postArray )
	{
		$command = parent::buildCommand( $postArray );

		$params = $this->getFormParams();

		// Extract the stack id from the stack string
		$stack = $params->getParamValue( "stack" );
		list($stackid, $apix, $boxsz, $totpart) = preg_split('%\|--\|%',$stack);
		$command = $this->removeCommandFlag( $command, "stack" );
		$command = $this->addCommandFlag( $command, "stack", "stack", $stackid );

		// Set the clip diameter
		$command = $this->removeCommandFlag( $command, "clip" );
		$clip = $params->getParamValue( "clip" );
		$bin  = $params->getParamValue( "bin" );
		if ( $clip == $boxsz ) {
			// no clipping needed
			$clip = '';
		} else {
			// clipping requested
			$clip = floor($clip/($bin*2.0))*2;
			$command.= " --clip=$clip ";
		}

		$flat  = ($params->getParamValue('flat') == 'on' ) ? true : false;
		if (!$flat) {
			$command.= " --flat ";
		}

		// If the commit box is checked, add --commit, otherwise --no-commit
		$commit  = ($params->getParamValue('commit') == 'on' ) ? true : false;
		if (!$commit) {
			$command.= " --no-commit ";
		}
		return $command;
	}

	// Override the validate function to add more complex validations than are available in the formValidator class.
	public function validate( $postArray )
	{
		$msg = parent::validate( $postArray );
		
		global $PROCESSING_HOSTS;
		echo "<br><br>processing hosts ".($PROCESSING_HOSTS[0]['host']->value);	

		$maxmem = $PROCESSING_HOSTS[0]['memorymax'];
//		$numnodes = $PROCESSING_HOSTS[0]['
		echo "mem max = ".$maxmem."<br><br>";
		var_dump($maxmem);
		$params = $this->getFormParams();
		$mpithreads = $params->getParamValue('mpithreads');
		$mpimem = $params->getParamValue('mpimem');
		$mpiprocs = $params->getParamValue('mpiprocs');			
		unset($PROCESSING_HOSTS);	
		
		// Extract the stack id from the stack string
		$stack = $params->getParamValue( "stack" );
		list($stackid, $apix, $boxsz, $totpart) = preg_split('%\|--\|%',$stack);

		$clip = $params->getParamValue('clip');

		if ($mpiprocs*$mpithreads*$mpimem > $maxmem) {
		$msg .= "<B>Error:</B> Total MPI threads per node * MPI memory/thread is greater than max memory per node. <br>( $mpiprocs procs/node * $mpithreads threads/proc * $mpimem Gb/thread = ".$mpiprocs*$mpithreads*$mpimem." Gb > $maxmem Gb )";
	
		return $msg;
		}

		if ($clip > $boxsz) {
			// Clip size too big
			$msg .= "<B>Error:</B> Clipping diameter ($clip pixels)"
			." must be less than or equal to the stack boxsize ($boxsz pixels)";
		}

		return $msg;
	}
}
?>