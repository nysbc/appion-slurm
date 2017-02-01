<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */
require_once "inc/particledata.inc";
require_once "inc/leginon.inc";

$sessionId= $_GET['Id'];
$minimum = $_GET['mconf'];
$viewdata = ($_GET['vd']==1) ? true : false;
$viewsql = ($_GET['vs']==1) ? true : false;

$ctf = new particledata();

$ctfinfo = $ctf->getBestCtfInfoByResolution($sessionId, $minimum);

if ($viewdata) {
	//Could use keys for a cleaner output
	$keys=array('filename','REF|leginondata|ScopeEMData|defocus','defocus1','defocus2','confidence','confidence_d','difference');
	echo dumpData($ctfinfo,$keys);
	//echo dumpData($ctfinfo);
}

if ($viewsql) {
	$sql = $ctf->mysql->getSQLQuery();
	echo $sql;
	exit;
}
?>
