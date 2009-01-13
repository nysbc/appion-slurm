<?php
/**
 *      The Leginon software is Copyright 2003 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
if ($_POST) {
	if ($_POST['projectId']) {
		$_SESSION['projectId']=$_POST['projectId'];
	}
}

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runUploadImage();
}

// Create the form page
else {
	createUploadImageForm();
}

function createUploadImageForm($extra=false, $title='UploadImage.py Launcher', $heading='Upload Images') {
	$particle = new particledata();
	// check if coming directly from a session
	$expId=$_GET['expId'];

	$projectId= $_SESSION['projectId'];
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
  
	processing_header($title,$heading,False,True);
	// write out errors, if any came up:
	if ($extra) {
		echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
	}
  
	echo"<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$outdir=$sessioninfo['Image path'];
		$outdir=ereg_replace("rawdata","",$outdir);
		$sessionname=$sessioninfo['Name'];
		$description=$sessioninfo['description'];
		$tem=$sessioninfo['InstrumentId'];
		$cam=$sessioninfo['CameraId'];
		echo "<input type='hidden' name='outdir' value='$outdir'>\n";
	}
	// Set any existing parameters in form
	$temval = ($_POST['tem']) ? $_POST['tem'] : $tem;
	$camval = ($_POST['cam']) ? $_POST['cam'] : $cam;
	$sessionname = ($_POST['sessionname']) ? $_POST['sessionname'] : $sessionname;
	$batch = ($_POST['batch']) ? $_POST['batch'] : $batch;
	$description = ($_POST['description']) ? $_POST['description']: $description;
	echo"
  <table border=3 class=tableborder>
  <tr>
    <td valign='TOP'>\n";
	echo"<table >
    <tr>
      <td valign='TOP'>";
	echo "
    <br/>\n
    <b>Project:</b><br/>
    <select name='projectId'>";
	$projectdata=new project();
	$projects=$projectdata->getProjects();
	foreach ($projects as $project) {
	$sel=($project['id']==$projectId) ? "selected" : "";
	echo "<option value='".$project['id']."' $sel >".$project['name']."</option>\n";
	}

	echo "</select><br>";
	echo "
    <b>Session Name:</b><br/>
    <input type='text' name='sessionname' value='$sessionname' size='65'><br />\n";
	echo"
      <p>
      <b>Session Description:</b><br/>
      <textarea name='description' rows='3' cols='65'>$description</textarea>
      </td>
    </tr>
		<tr>
			<td>";
	$leginondata = new leginondata();
	$instrumenthosts = $leginondata->getInstrumentHosts();
	$instrumenthostval = ($_POST[instrumenthost]) ? $_POST[instrumenthost] : $instrumenthosts[0];
	echo "
		Host
		<select name='instrumenthost' onchange=submit()>";
	foreach($instrumenthosts as $host) {
		$s = ($instrumenthostval==$host) ? 'selected' : 'not';
		echo "<option value=".$host." ".$s.">".$host."</option>\n";
	}
	echo"
		</select>";
	$scopes = $leginondata->getScopes($instrumenthostval);
	$cameras = $leginondata->getCameras($instrumenthostval);
	echo "
		Scope
		<select name='tem' onchange=submit()>";
	foreach($scopes as $sc) {
		$s = ($temval==$sc['id']) ? 'selected' : '';
		echo "<option value=".$sc['id']." ".$s." >".$sc['name']."</option>";
	}
	echo"
		</select>
		Camera
		<select name='cam' onchange=submit()>";
	foreach($cameras as $c) {
		echo $c['id'];
		$s = ($camval==$c['id']) ? 'selected' : 'not';
		echo "<option value=".$c['id']." ".$s." >".$c['name']."</option>";
	}
	echo"
		</select>";
	echo "
      <p>
      <b>Information File Name:</b><br/>
      <input type='text' name='batch' value='$batch' size='65'><br />\n";
	echo "
      </td>
    </tr>
  <tr>
    <td align='CENTER'>
      <hr>
	";
	echo getSubmitForm("Upload Image");
	echo "
        </td>
	</tr>
  </table>
  </form>\n";

	processing_footer();
	exit;
}

function runUploadImage() {
	$expId = $_POST['expId'];
	$sessionname = $_POST['sessionname'];
	$batch = $_POST['batch'];
	$tem = $_POST['tem'];
	$cam = $_POST['cam'];
	
	$outdir = $_POST['outdir'];

	$command = "uploadimage.py ";
	$command.="--projectid=".$_SESSION['projectId']." ";

	//make sure a session name was entered if upload an independent file
	if (!$sessionname) createUploadImageForm("<B>ERROR:</B> Enter a session name of the image");

	//make sure a information batch file was provided
	if (!$batch) createUploadImageForm("<B>ERROR:</B> Enter a batch file with path");
  
	// make sure there are valid instrument
	if (!$tem) createUploadImageForm("<B>ERROR:</B> Choose a tem where the images are acquired");
	if (!$cam) createUploadImageForm("<B>ERROR:</B> Choose a camera where the images are acquired");

	//make sure a description was provided
	$description=$_POST['description'];
	if (!$description) createUploadImageForm("<B>ERROR:</B> Enter a brief description of the session");


	$command.="--session=$sessionname ";
	$command.="--batch=$batch ";	
	$command.="--tem=$tem ";	
	$command.="--cam=$cam ";	
	$command.="--description=\"$description\" ";
	
	// submit job to cluster
	if ($_POST['process']=="Upload Images") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createUploadImageForm("<B>ERROR:</B> You must be logged in to submit");

		$sub = submitAppionJob($command,$outdir,$sessionname,$expId,'uploadimage',True);
		// if errors:
		if ($sub) createUploadImageForm("<b>ERROR:</b> $sub");

		// check that upload finished properly
		$jobf = $outdir.'/'.$sessionname.'/'.$runname.'.appionsub.log';
		$status = "Images were uploaded";
		if (file_exists($jobf)) {
			$jf = file($jobf);
			$jfnum = count($jf);
			for ($i=$jfnum-5; $i<$jfnum-1; $i++) {
			  // if anything is red, it's not good
				if (preg_match("/red/",$jf[$i])) {
					$status = "<font class='apcomment'>Error while uploading, check the log file:<br />$jobf</font>";
					continue;
				}
			}
		}
		else $status = "Job did not run, contact the appion team";
		processing_header("Image Upload", "Image Upload");
		echo "$status\n";
	}

	else processing_header("UploadImage Command","UploadImage Command");
	
	// rest of the page
	echo"
	<table width='600' border='1'>
	<tr><td colspan='2'>
	<b>UploadImage Command:</b><br/>
	$command
	</td></tr>
	<tr><td>batch file</td><td>$batch</td></tr>
	<tr><td>tem id</td><td>$tem</td></tr>
	<tr><td>camera id</td><td>$cam</td></tr>
	<tr><td>session</td><td>$sessionname</td></tr>
	<tr><td>description</td><td>$description</td></tr>
	</table>\n";
	processing_footer();
}
?>
