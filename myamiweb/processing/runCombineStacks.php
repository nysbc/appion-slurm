<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/processing.inc";
require "inc/summarytables.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST) {
	runCombineStack();
} else {
	createCombineStackForm();
}

function createCombineStackForm($extra=false, $title='combinestack.py Launcher', $heading='Combine Stack') {
	$expId = $_GET['expId'];
	$projectId = (int) getProjectFromExpId($expId);
	//echo "Project ID: ".$projectId." <br/>\n";
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	if ($_GET['showHidden']) $formAction.="&showHidden=True";

	$javascript.= editTextJava();

	processing_header($title, $heading, $javascript, False);
	// write out errors, if any came up:
	if ($extra)
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";

	// --- Get Stack Data --- //
	$particle = new particledata();
	$stackids = $particle->getStackIdsForProject($projectId, False);
	$description = $_POST['description'];
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","stacks/",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}
	$outdir = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;

	$stackruninfos = $particle->getStackIds($expId, True);
	$stackruns = ($stackruninfos) ? count($stackruninfos) : 0;
	while (file_exists($sessionpathval.'stack'.($stackruns+1)))
		$stackruns += 1;
	$runname = ($_POST['runname']) ? $_POST['runname'] : 'combine'.($stackruns+1);

	if ($stackids) {
		echo "<form name='stackform' method='post' action='$formAction'>\n";
		echo "<table border='1'>";
		echo "<tr><td colspan='4'><h2>New stack info:</h2>\n";
		echo docpop('runname','<b>Combined stack name:</b>');
		echo "<br/>\n";
		echo "<input type='text' name='runname' value='$runname'>\n";
		echo "<br/>\n";
		echo docpop('outdir','<b>Output Directory:</b>');
		echo "<br />\n";
		echo "<input type='text' name='outdir' value='$outdir' size='50'>\n";
		echo "<br />\n";
		echo docpop('descr','<b>Description of combined stack:</b>');
		echo "<br/>\n";
		echo "<textarea name='description' rows='3' cols='50'>$description</textarea>\n";
		echo "<br/>\n";
		echo getSubmitForm("Run Combine Stack");
		echo "</td></tr>\n";
		echo "<tr><td colspan='4'><h2>Select stacks to combine:</h2>\n";
		echo "</td></tr>\n";

		// sort stacks by session
		$sessionids = array();
		$stacknums = array();
		foreach ($stackids as $stackdata) {
			$stackid = (int) $stackdata['stackid'];
			$stacknums[] = $stackid;
			$selectdata = $particle->getStackSelectionRun($stackid);
			$sessionid = (int) $selectdata[0]['sessionId'];
			$sessionids[] = $sessionid;
		}
		array_multisort($sessionids, SORT_DESC, $stacknums, SORT_DESC);
		$currsessionid = 0;
		foreach ($stacknums as $stackid) {
			$selectdata = $particle->getStackSelectionRun($stackid);
			$sessionid = (int) $selectdata[0]['sessionId'];
			if ($currsessionid != $sessionid) {
				$currsessionid = $sessionid;
				$sessiondata = $particle->getSessionData($sessionid);
				echo "<tr><td colspan='4'><font size='+1'><br/>Session: ";
				echo "<a href='index.php?expId=".$sessiondata['DEF_id']."'>".$sessiondata['name']."</a></font>&nbsp;\n";
				echo " --  ".$sessiondata['comment'];
				echo "<br/><br/></td></tr>";
			}
			//echo "<br/><br/><br/><br/>";
			echo "<tr><td>\n<input type='checkbox' name='stack$stackid'";
			if ($_POST['stack'.$stackid]) echo " checked";
			echo ">combine<br/>stack id $stackid\n</td><td>\n";
			echo ministacksummarytable($stackid);
			echo "</td></tr>\n";
		}
		echo "</table>";
		echo "</form>";
	} else {
		echo "<B>Project does not contain any stacks.</B>\n";
	}

	processing_footer();
	exit;
}

function runCombineStack() {
	$expId = $_GET['expId'];
	$projectId = (int) getProjectFromExpId($expId);
	$runname=$_POST['runname'];
	$outdir=$_POST['outdir'];

	$command.="combinestack.py ";
	$command.="--projectid=".getProjectId()." ";
	
	//make sure a session was selected
	$description=$_POST['description'];
	if (!$description) createCombineStackForm("<B>ERROR:</B> Enter a brief description");

	$particle = new particledata();
	$stackids = $particle->getStackIdsForProject($projectId, False);
	$stacklist = "";
	$count = 0;
	$stacks = array();
	foreach ($stackids as $stackdata) {
		$stackid = $stackdata['stackid'];
		$key = 'stack'.$stackid;
		//$stacklist .= $key.": ".$_POST[$key]."<br/>\n";
		if ($_POST[$key] == 'on') {
			$count++;
			$stacks[]=$stackid;
		}
	}
	$stacklist = implode(',',$stacks);
	if (strlen($stacklist) < 1) 
		createCombineStackForm("<B>ERROR:</B> No stacks selected ".$count.": ".$stacklist);
	if ($count < 2) 
		createCombineStackForm("<B>ERROR:</B> Selected more than one stack");

	if ($outdir) {
		// make sure outdir ends with '/' and append run name
		if (substr($outdir,-1,1)!='/') $outdir.='/';
		$rundir = $outdir.$runname;
		$command.="--rundir=$rundir ";
	}
	$command.="--runname=$runname ";
	$command.="--stacks=$stacklist ";
	$command.="--description=\"$description\" ";
	$command.="--commit ";

	// submit job to cluster
	if ($_POST['process']=="Run Combine Stack") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createCombineStackForm("<B>ERROR:</B> Enter a user name and password");

		$sub = submitAppionJob($command,$outdir,$runname,$expId,'makestack');
		// if errors:
		if ($sub) createCombineStackForm("<b>ERROR:</b> $sub");
		exit;
	} else {
		processing_header("Combine Stack Params","Combine Stack  Params");
		echo"
		<table width='600' class='tableborder' border='1'>
		<tr><td colspan='2'>
		<b>Combine Stack Command:</b><br />
		$command
		</td></tr>
		<tr><td>run id</td><td>$runname</td></tr>
		<tr><td>run id</td><td>$description</td></tr>
		<tr><td>stack ids</td><td>$stackids</td></tr>
		<tr><td>out dir</td><td>$rundir</td></tr>
		<tr><td>commit</td><td>$commit</td></tr>
		</table>\n";
		processing_footer();
	}
	exit;
}



?>
