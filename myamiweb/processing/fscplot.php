<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

include ("inc/particledata.inc");
include ("inc/jpgraph.php");
include ("inc/jpgraph_utils.inc");
include ("inc/jpgraph_line.php");
include ("inc/jpgraph_scatter.php");
require ("inc/leginon.inc");

$fsc=$_GET['fscfile'];
$width=$_GET['width'];
$height=$_GET['height'];
$nomargin=$_GET['nomargin'];
$apix=$_GET['apix'];
$box=$_GET['box'];

if (!$width || !$height){
	$width=800;
	$height=600;
}

if (!$apix) $apix=1;
if (!$box) $box=100;

$data = file($fsc);

$sx = array();
$sy = array();
if (is_array($data))
	foreach ($data as $line) {
		$line=rtrim($line);
		list($x,$sy[])=split("\t",$line);
		$sx[]=$x;
		// convert pixels to resolution in angstroms
		$xpix[]=sprintf("%.2f",$box*$apix/$x);
	}

// Setup the basic graph
$graph = new Graph($width,$height,"auto");
//$graph->SetScale("linlin");

$last=end($sx);
$graph->SetAlphaBlending();

if (!$nomargin) {
  $graph->SetScale("linlin",0,'auto',$sx[0],$last);
  $graph->img->SetMargin(50,40, 30,70);	
	$graph->title->Set('Fourier Shell Correlation ');
	$graph->xaxis->SetTitlemargin(30);
	$graph->xaxis->title->Set("Resolution (A/pix)");
	$graph->yaxis->SetTitlemargin(35);
	$graph->yaxis->title->Set("Correlation");
	$graph->xaxis->SetTickLabels($xpix);
	$graph->AddLine(new PlotLine(HORIZONTAL,0.5,"black",1));
}
else {
  $graph->SetScale("intlin",0,'auto',$sx[0],$last);
  $graph->img->SetMargin(2,4,4,4);	
	$graph->ygrid->Show(false,false);
	$graph->xgrid->Show(false,false);
	$graph->xaxis->Hide(true);
	$graph->AddLine(new PlotLine(HORIZONTAL,0,"black",1));
}  

$lp1 = new LinePlot($sy,$sx);
$lp1->SetColor('blue');
$lp1->SetWeight(1);

$graph->Add($lp1);

$graph->Stroke();

?>
