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
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/appionloop.inc";
require "inc/ctf.inc";
//require "inc/ssh.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runPyAce();
}
// CREATE FORM PAGE
else {
	createPyAceForm();
}

/*
$expId = $_GET[expId];
$phpself=$_SERVER['PHP_SELF'];

// --- Set sessionId
if ($expId){$sessionId=$expId;}
else {$sessionId=$_POST[sessionId];}

$projectId =$_POST[projectId];

$projectdata = new project();
$projectdb = $projectdata->checkDBConnection();

if($projectdb)
	$projects = $projectdata->getProjects('all');

if(!$sessions)
	$sessions = $leginondata->getSessions('description', $projectId);

$sessioninfo = $leginondata->getSessionInfo($sessionId);
$presets = $leginondata->getTruePresets($sessionId);

if (!empty($sessioninfo)) {
	$sessionpath=$sessioninfo['Image path'];
	$sessionpath=ereg_replace("leginon","appion",$sessionpath);
	$sessionpath=ereg_replace("rawdata","pyAce/",$sessionpath);
	$sessionname=$sessioninfo['Name'];
}

// --- find hosts to run ACE
$path = "/var/lib/wwwrun/.ssh/";
$result=array();
foreach($hosts as $host) {
	list($str) = split(" ", $host); 
	list($str) = split(",", $str); 
	$hosts_select[]=$str;
}
*/

// --- parse data and process on submit
function runPyAce() {
	$edgethcarbon=$_POST[edgethcarbon];
	$edgethice=$_POST[edgethice];
	$pfcarbon=$_POST[pfcarbon];
	$pfice=$_POST[pfice];
	$overlap=$_POST[overlap];
	$fieldsize=$_POST[fieldsize];
	$resamplefr=$_POST[resamplefr];
	//$tempdir=$_POST[tempdir];
	$medium=$_POST[medium];
	$cs=$_POST[cs];
	$outdir=$_POST[outdir];
	$nominal=$_POST[nominal];
	$reprocess=$_POST[reprocess];
	$display = ($_POST[display]=="on") ? "1" : '0';
	$newnominal = ($_POST[newnominal]=="on") ? "1" : '0';
	$drange = ($_POST[drange]=="on") ? "1" : '0';
	$stig = ($_POST[stig]=="on") ? "1" : '0';
	$continue = ($_POST[cont]=="on") ? "1" : '0';
	$commit = ($_POST[commit]=="on") ? "1" : '0';
	$proc = $_POST[processor];

	//$command ="source /ami/sw/ami.csh;";
	//$command.="source /ami/sw/share/python/usepython.csh common32;";
	//$command.="source /home/$user/pyappion/useappion.csh;";
	//$command.="alias matlab /ami/sw/packages/matlab72/bin/matlab;";
	//$command.="cd /home/$user/pyappion/ace/;";

	$command.="pyace.py ";
	$command.="edgethcarbon=$edgethcarbon ";
	$command.="edgethice=$edgethice ";
	$command.="pfcarbon=$pfcarbon ";
	$command.="pfice=$pfice ";
	$command.="overlap=$overlap ";
	$command.="fieldsize=$fieldsize ";
	$command.="resamplefr=$resamplefr ";
	//$command.="tempdir=$tempdir ";
	$command.="medium=$medium ";
	$command.="cs=$cs ";
	$command.="drange=$drange ";
	$command.="display=$display ";
	$command.="stig=$stig";
	if ($nominal) $command.=" nominal=$nominal";
	if ($reprocess) $command.=" reprocess=$reprocess";
	if ($newnominal) $command.=" newnominal";
	$apcommand = parseAppionLoopParams($_POST);
	if ($apcommand[0] == "<") {
		createPyAceForm($apcommand);
		exit;
	}
	$command .= $apcommand;

	writeTop("PyACE Results","PyACE Results");

	echo"
	<P>
	<TABLE WIDTH='600'>
	<TR><TD COLSPAN='2'>
	<B>ACE Command:</B><br/>
	$command<HR>
	</TD></TR>";
	appionLoopSummaryTable();
	echo"
	<TR><TD>edgethcarbon</TD><TD>$edgethcarbon</TD></TR>
	<TR><TD>edgethice</TD><TD>$edgethice</TD></TR>
	<TR><TD>pfcarbon</TD><TD>$pfcarbon</TD></TR>
	<TR><TD>pfice</TD><TD>$pfice</TD></TR>
	<TR><TD>overlap</TD><TD>$overlap</TD></TR>
	<TR><TD>fieldsize</TD><TD>$fieldsize</TD></TR>
	<TR><TD>resamplefr</TD><TD>$resamplefr</TD></TR>
	<TR><TD>medium</TD><TD>$medium</TD></TR>
	<TR><TD>cs</TD><TD>$cs</TD></TR>
	<TR><TD>drange</TD><TD>$drange</TD></TR>
	<TR><TD>display</TD><TD>$display</TD></TR>
	<TR><TD>stig</TD><TD>$stig</TD></TR>\n";

	if ($nominal=="db value" OR $nominal=="") echo "<TR><TD>nominal</TD><TD><I>NULL</I></TD></TR>\n";
	else echo "<TR><TD>nominal</TD><TD>$nominal</TD></TR>\n";
	if ($reprocess) echo "<TR><TD>reprocess</TD><TD>$reprocess</TD></TR>\n";
	else echo "<TR><TD>reprocess</TD><TD><I>NULL</I></TD></TR>\n";
	echo "<TR><TD>newnominal</TD><TD>$newnominal</TD></TR>\n";
	echo "</TABLE>\n";
	writeBottom();
}

/*
**
**
** PyACE FORM
**
**
*/

// CREATE FORM PAGE
function createPyAceForm($extra=false) {
	// check if coming directly from a session
	$expId = $_GET['expId'];
	if ($expId) {
		$sessionId=$expId;
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	}
	else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF'];	
	}
	$projectId=$_POST['projectId'];

	// --- find hosts to run PyACE
	$hosts = getHosts();
	$users[]="glander";

	$presetval = ($_POST['preset']) ? $_POST['preset'] : 'en';
	$javafunctions="
	<script src='../js/viewer.js'></script>
	<script LANGUAGE='JavaScript'>
		function enabledf(){
			 if (document.viewerform.nominalcheck.checked){
			    document.viewerform.nominal.disabled=false;
			    document.viewerform.nominal.value='';
			 }
			 else {
			    document.viewerform.nominal.disabled=true;
			    document.viewerform.nominal.value='db value';
			 }
		}
		function enableconf(){
			 if (document.viewerform.confcheck.checked){
			    document.viewerform.reprocess.disabled=false;
			    document.viewerform.reprocess.value='';
			 }
			 else {
			    document.viewerform.reprocess.disabled=true;
			    document.viewerform.reprocess.value='0.8';
			 }
		}
		function infopopup(infoname){
			var newwindow=window.open('','name','height=250,width=400');
			newwindow.document.write('<HTML><BODY>');
			if (infoname=='edgethresh'){
				newwindow.document.write('The threshold set for edge detection. ACE searches a range of values to determine a good threshold, but this value should be increased if there are more edges in the power spectrum than in the ring.  Decrease if no edges are detected.');
			}
			if (infoname=='pfact'){
				newwindow.document.write('Location of the upper cutoff frequency.  If thon rings extend beyond the power spectrum cutoff frequency, increase this value.  In cases of low signal to noise ratio with few thon rings, decrease this value.')
			}
			if (infoname=='drange'){
				newwindow.document.write('Use in cases where the signal to noise ratio is so high that the edge detection is incorrect.');
			}
			if (infoname=='resamplefr'){
				newwindow.document.write('Sets the sampling size of the CTF.  At high defoci or at higher magnifications, the first thon rings may be so close to the origin that they are not processed by ACE. In these cases raise the resampling value (2.0 works well in these cases).<br/><br/><TABLE><TR><TD COLSPAN=2>typical values for defocus/apix</TD></TR><TR><TD>0.5</TD><TD>1.2</TD></TR><TR><TD>1.0</TD><TD>1.5</TD></TR><TR><TD>1.5</TD><TD>1.6</TD></TR><TR><TD>2.0</TD><TD>1.8</TD></TR><TR><TD>3.0</TD><TD>2.2</TD></TR><TR><TD>4.0</TD><TD>2.7</TD></TR></TABLE><br/>For example, with defocus = 2.0 (-2.0x10<SUP>-6</SUP> m) and apix (&Aring;/pixel) = 1.63<br/>then defocus/apix = 1.22 and you should use resamplefr=1.6<br/>(as long as its close it should work.)');
			}
			if (infoname=='overlap'){
				newwindow.document.write('During processing, micrographs are cut into a series of smaller images and averaged together to increase the signal to noise ratio. This value (n) will result in successive images having an overlap of (1-n)*field size. Increase in cases of very low signal to noise ratio.');
			}
			if (infoname=='field'){
				newwindow.document.write('During processing, micrographs are cut into a series of smaller images and averaged together to increase the signal to noise ratio. This value refers to the width (in pixels) of the cropped images.');
			}
			newwindow.document.write('</BODY></HTML>');
			newwindow.document.close();
		}

	</SCRIPT>\n";
	$javafunctions .= appionLoopJavaCommands();
	writeTop("PyACE Launcher","Automated CTF Estimation With PyACE",$javafunctions);

	if ($extra) {
		echo "<FONT COLOR='#DD0000' SIZE=+2>$extra</FONT>\n<HR>\n";
	}
	echo"
	<FORM NAME='viewerform' method='POST' action='$phpself'>\n";
	$sessiondata=displayExperimentForm($projectId,$sessionId,$expId);
	$sessioninfo=$sessiondata['info'];
	$presets=$sessiondata['presets'];
	if (!empty($sessioninfo)) {
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","pyAce/",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}
	$ctf = new ctfdata();
	$ctfruns = count($ctf->getCtfRunIds($sessionId));
	$defrunid = 'acerun'.($ctfruns+1);
	echo"
	<P>
	<TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
	<TR>
	  <TD VALIGN='TOP'>";

	createAppionLoopTable($sessiondata, $defrunid, "pyAce");
	echo"
	  </TD>
	  <TD CLASS='tablebg'>

	    <INPUT TYPE='checkbox' NAME='display' CHECKED>
	    Write Result Images<br/>
	    <br/>
	    <B>Medium:</B><br/>
	    <INPUT TYPE='radio' NAME='medium' VALUE='carbon'>&nbsp;carbon&nbsp;&nbsp;
	    <INPUT TYPE='radio' NAME='medium' VALUE='ice' checked>&nbsp;ice<br/>
	    <br/>

	    <B>Astigmatism:</B><br/>
	    <INPUT TYPE='checkbox' NAME='stig'>
	    Estimate Astigmatism <FONT SIZE=-2><I>(experimental)</I></FONT><br/>
	    <br/>

	  <TABLE CELLSPACING=0 CELLPADDING=2><TR>

	    <TD VALIGN='TOP'>
	    <A HREF=\"javascript:infopopup('edgethresh')\"><B>Edge Thresholds:</B></A><br/>
	    <INPUT TYPE='text' NAME='edgethcarbon' VALUE='0.8' SIZE='4'>
	    Carbon<br/>
	    <INPUT TYPE='text' NAME='edgethice' VALUE='0.6' SIZE='4'>
	    Ice
	    </TD>

	    <TD VALIGN='CENTER'>&nbsp;</TD>
	    <TD VALIGN='CENTER'>&nbsp;</TD>

	    <TD VALIGN='TOP'>
	    <A HREF=\"javascript:infopopup('pfact')\"><B>Power Factors:</B></A><br/>
	    <INPUT TYPE='text' NAME='pfcarbon' VALUE='0.9' SIZE='4'>
	    Carbon<br/>
	    <INPUT TYPE='text' NAME='pfice' VALUE='0.3' SIZE='4'>
	    Ice
	    </TD>

	  </TR></TABLE><br/>

	    <INPUT TYPE='text' NAME='resamplefr' VALUE='1.5' size='4'>
	    <A HREF=\"javascript:infopopup('resamplefr')\">Resampling Frequency</A><br/>

	    <INPUT TYPE='text' NAME='overlap' VALUE='2' SIZE='4'>
	    <A HREF=\"javascript:infopopup('overlap')\">Averaging Overlap</A><br/>

	    <INPUT TYPE='text' NAME='fieldsize' VALUE='512' size='4'>
	    <A HREF=\"javascript:infopopup('field')\">Field Size</A><br/>

	    <INPUT TYPE='text' NAME='cs' VALUE='2.0' SIZE='4'>
	    Spherical Aberration<br/>

	    <INPUT TYPE='checkbox' NAME='drange'>
	    <A HREF=\"javascript:infopopup('drange')\">Compress Dynamic Range</A><br/>
	    <br/>

	    <INPUT TYPE='checkbox' NAME='confcheck' onclick='enableconf(this)'>
	    Reprocess Below Confidence Value<br/>
	    Set Value:<INPUT TYPE='text' NAME='reprocess' DISABLED VALUE='0.8' SIZE='4'>
	    <FONT SIZE=-2><I>(between 0.0 - 1.0)</I></FONT><br/>
	    <br/>

	    <B>Nominal override:</B><br/>
	    <INPUT TYPE='checkbox' NAME='nominalcheck' onclick='enabledf(this)'>
	    Override Nominal Defocus<br/>
	    Set Defocus:<INPUT TYPE='text' NAME='nominal' DISABLED VALUE='db value' SIZE='8'>
	    <FONT SIZE=-2><I>(in meters, i.e. <B>-2.0e-6</B>)</I></FONT><br/>";
	if ($ctfruns > 0) {
		echo"
			<INPUT TYPE='checkbox' NAME='newnominal'>
	    Use Previously ACE Estimated Defocus";
	}
	echo"
	  </TD>
	</TR>
	<TR>
	  <TD COLSPAN='2' ALIGN='CENTER'>\n<HR>\n";
/*
	  Host: <select name='host'>\n";
	foreach($hosts as $host) {
		$s = ($_POST['host']==$host) ? 'selected' : '';
		echo "<option $s >$host</option>\n";
	}
	echo "</select>\nUser: <select name='user'>\n";
	foreach($users as $user) {
		$s = ($_POST['user']==$user) ? 'selected' : '';
		echo "<option $s >$user</option>\n";
	}
	echo"</select>";*/
	echo"<br/>
	  <input type='submit' name='process' value='Generate ACE Command'><br/>
	  <FONT COLOR='RED' SIZE='-1'>Submission will NOT run ACE,<BR/>
		only output a command that you can copy and paste into a unix shell</FONT>
	  </TD>
	</TR>
	</TABLE>
	</FORM>\n";
	writeBottom();
}

function getdata($str_field, $str_data) {
	$result=array();
	$f = explode(" ",$str_field);
	foreach($f as $k=>$v) {
		if ($v)
			$fields[]=$v;
	}
	foreach($fields as $k=>$f) {
		$positions[] = ($k) ? strpos($str_field, $f) : 0;
	}
	foreach ($positions as $k=>$v) {
		$l = ($k<count($positions)-1) ? $positions[$k+1]-$v : strlen($str_data);
		$f = $fields[$k];
		$result[$f]=trim(substr($str_data, $v, $l));
	}
	return $result;
}


?>
