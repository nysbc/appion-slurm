<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Display results for each iteration of a refinement
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/summarytables.inc";
  
// check if reconstruction is specified
if (!$tomoId = $_GET['tomoId'])
	$tomoId=false;
$expId = $_GET['expId'];

$align_params_fields = array('alignrun','bin','name');
$javascript="<script src='../js/viewer.js'></script>\n";

// javascript to display the refinement parameters
$javascript="<script LANGUAGE='JavaScript'>
        function infopopup(";
foreach ($align_params_fields as $param) {
        if (ereg("\|", $param)) {
	        $namesplit=explode("|", $param);
		$param=end($namesplit);
	}
	$alignstring.="$param,";
}
$alignstring=rtrim($refinestring,',');
$javascript.=$alignstring;
$javascript.=") {
                var newwindow=window.open('','name','height=400, width=200, resizable=1, scrollbar=1');
                newwindow.document.write(\"<HTML><HEAD><link rel='stylesheet' type='text/css' href='css/viewer.css'>\");
                newwindow.document.write('<TITLE>Ace Parameters</TITLE>');
                newwindow.document.write(\"</HEAD><BODY><TABLE class='tableborder' border='1' cellspacing='1' cellpadding='5'>\");\n";
foreach($align_params_fields as $param) {
	if (ereg("\|", $param)) {
		$namesplit=explode("|", $param);
		$param=end($namesplit);
	}
	$javascript.="                if ($param) {\n";
	$javascript.="                        newwindow.document.write('<TR><TD>$param</TD>');\n";
	$javascript.="                        newwindow.document.write('<TD>'+$param+'</TD></TR>');\n";
	$javascript.="                }\n";
}
$javascript.="                newwindow.document.write('</TABLE></BODY></HTML>');\n";
$javascript.="                newwindow.document.close()\n";
$javascript.="        }\n";
$javascript.="</script>\n";

$javascript.=eulerImgJava(); 

processing_header("Tomogram Report","Tomogram Report Page", $javascript);
if (!$tomoId) {
	processing_footer();
	exit;
}

// --- Get Reconstruction Data
$particle = new particledata();
$tomogram = $particle->getTomogramInfo($tomoId);
$tiltparams = $particle->getTiltSeriesInfo($tomogram['tiltseries']);
// get pixel size
$apix=$tomogram['pixelsize']*1e10;
$html .= "<BR>\n<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
$title = "tomogram info";
$tomograminfo = array(
	'id'=>$tomogram['DEF_id'],
	'name'=>$tomogram['name'],
	'description'=>$tomogram['description'],
	'path'=>$tomogram['path'],
);
if ($tomogram['centerx']) {
	$tomograminfo = array_merge_recursive($tomograminfo,
		array(
			'center'=>'('.$tomogram['centerx'].','.$tomogram['centery'].')',
			'dimension'=>'('.$tomogram['dx'].','.$tomogram['dy'].')',
			'full tomogram id'=>$tomogram['full'],
			'alignment package'=>$tomogram['align'],
		)
	);
}
echo "<table><tr><td colspan=2>\n";
$particle->displayParameters($title,$tomograminfo,array(),$expId);
echo "</td></tr>";
//SnapShot
$snapshotfile = $tomogram['path']."/snapshot.png";
if (file_exists($snapshotfile)) {
	echo "<tr><td>";
	echo "<a href='loadimg.php?filename=$snapshotfile' target='snapshotfile'>"
		."<img src='loadimg.php?filename=$snapshotfile&s=180' height='180'><br/>\nSnap Shot</a>";
	echo "</td>";
}
//FlashMovie
$moviefile = $tomogram['path']."/minitomo.flv";
if (file_exists($moviefile)) {
	echo "<td>";
	echo "<a href='loadimg.php?filename=$moviefile' target='snapshotfile'>"
		."<img src='loadimg.php?filename=$moviefile&s=180' height='180'><br/>\nMovie</a>";
	echo "</td></tr>";
}

echo "</table>";
echo $html;

processing_footer();
?>
