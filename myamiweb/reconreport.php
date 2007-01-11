<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */

require ('inc/leginon.inc');
require ('inc/particledata.inc');
require ('inc/project.inc');
require ('inc/viewer.inc');
require ('inc/processing.inc');
  
// check if reconstruction is specified
$reconId = $_GET['reconId'];

$javascript="<script src='js/viewer.js'></script>\n";

writeTop("Reconstruction Report","Reconstruction Report Page", $javascript);

// --- Get Reconstruction Data
$particle = new particledata();
$html = "<BR>\n<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
$html .= "<TR>\n";
$display_keys = array ( 'iteration', 'ang incr', 'resolution', 'mask', 'fourier padding','density');
foreach($display_keys as $key) {
        $html .= "<TD><span class='datafield0'>".$key."</span> </TD> ";
}
$iterations = $particle->getIterationInfo($reconId);
foreach ($iterations as $iteration){
        $res = $particle->getResolutionInfo($iteration['REF|resolution|resolutionId']);
	$halfres = sprintf("%.2f",$res['half']);
	$halfres = ($halfres==0) ? $halfres='None' : $halfres;
	$html .= "<TR>\n";
	$html .= "<TD>$iteration[iteration]</TD>\n";
	$html .= "<TD>$iteration[angIncr]</TD>\n";
	$html .= "<TD>$halfres</TD>\n";
	$html .= "<TD>$iteration[mask]</TD>\n";
	$html .= "<TD>$iteration[fourier_padding]</TD>\n";
	$html .= "<TD>$iteration[volumeDensity]</TD>\n";
	$html .= "</TR>\n";
}

echo $html;

writeBottom();
?>
