<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	refinement selection form
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/processing.inc";

$expId = $_GET['expId'];
$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

processing_header("Reconstruction Refinement Software Selection","Refinement Software Selection Page", $javascript,False);

// Selection Header
echo "<table border='0' width='640'>\n";
echo "<tr><td>\n";
echo "  <h2>Reconstruction Refinement Procedures</h2>\n";
echo "  <h4>\n";
echo "    Most initial models establish a preliminary sense of the overall shape of " 
	."the biological specimen. To reveal structural information that can answer specific "
	."biological questions, the model requires refining. In single particle analysis, a refinement "
	."is an iterative procedure, which sequentially aligns the raw particles, assign to them appropriate "
	."spatial orientations (Euler angles) by comparing them against the a model, and then back-projects "
	."them into 3D space to form a new model. Effectively, a full refinement takes as input a raw particle "
	."stack and an initial model and is usually carried out until no further improvement of the structure can "
	."be observed.\n";
echo "  </h4>\n";
echo "</td></tr>\n";
echo "</table>\n";


echo "<br/>\n";
echo "<table border='1' class='tableborder' width='640'>\n";


/*
** EMAN1 projection-matchign refinement protocol
*/
echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/eman_logo.png' width='64'>\n";
echo "</td><td>\n";
echo "  <h3><a href='selectStackForm.php?expId=$expId&method=eman'>EMAN1 projection-matching refinement</a></h3>\n";
echo "<p>This is one of the original projection-matching refinement protocols, as implemented in "
	."<a href='http://blake.bcm.tmc.edu/eman/eman1/'>EMAN.</a>&nbsp;<img src='img/external.png'> It has been successfully "
	."tested on many different samples. Within each iteration, the raw particles are classified according to the angular "
	."sampling of projection directions, then iteratively aligned within each class to reduce the model bias. "
	."Further classification and particle 'filtering' has been incorporated using a SPIDER protocol that identifies "
	."and removes the particles with the highest variance (and therefore least correspondence) in the class using the "
	."<a href='http://www.wadsworth.org/spider_doc/spider/docs/man/cas.html'>"
	."CA S</a>&nbsp;<img src='img/external.png'> correspondence analysis operation in spider."
	."</p>\n";
echo "</td></tr>\n";

/*
** Xmipp projection-matching refinement protocol
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/xmipp_logo.png' width='64'>\n";
echo "</td><td>\n";
echo "  <h3><a href='selectStackForm.php?expId=$expId&method=xmipp'>Xmipp projection-matching refinement</a></h3>\n";
echo " <p> This is the <a href='http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/ProjectionMatchingRefinement'>
	Xmipp projection-matching refinement protocol.</a>&nbsp;<img src='img/external.png'> The classification of "
	."raw particles is done using the <a href='http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/Projection_matching'>
	angular projection matching</a>&nbsp;<img src='img/external.png'>&nbsp;"
	."operation in Xmipp. The user is given the option of employing an algebraic reconstruction technique "
	."(ART), weighted back-projection (WBP) or Fourier interpolation method to recontruct the computed classes from "
	."projection-matching. One big advantage to this protocol is speed. Because all Euler angle and alignment parameters "
	."are saved for each iteration of angular projection-matching, the later iterations localize the search space "
	."to an increasingly narrow region and, therefore, take significantly less cpu time to complete. "
	."</p>\n";
//echo "  <img src='img/align-smr.png' width='250'><br/>\n";
echo "</td></tr>\n";

/*
** Frealign projection-matching refinement protocol
*/
echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/grigorieff_lab.png' width='96'>\n";
echo "</td><td>\n";
echo "  <h3><a href='selectStackForm.php?expId=$expId&method=frealign'>Frealign projection-matching refinement</a></h3>\n";
echo "<p>The <a href='http://emlab.rose2.brandeis.edu/frealign'>Frealign</a>&nbsp;<img src='img/external.png'> "
	."(Fourier REconstruction and ALIGNment) projection-matching refinement protocol has been designed to refine a stack "
	."of particles for which the alignment and classification parameters are approximately known. It therefore also "
	."relies on a good initial model. The algorithms used in the Frealign package are designed to extract "
	."as much high resolution information out of the data as possible."
	."</p>\n";
echo "</td></tr>\n";

if (!HIDE_FEATURE)
{
	/*
	** SPIDER Reference Based Alignment
	*/
	
	echo "<tr><td width='100' align='center'>\n";
	echo "  <img src='img/spider_logo.png' width='64'>\n";
	echo "</td><td>\n";
	echo "  <h3><a href='selectStackForm.php?expId=$expId&method=spider'>Spider Refinement</a></h3>\n";
	echo " <p> first you select template and then this method uses the "
		."<a href='http://www.wadsworth.org/spider_doc/spider/docs/man/apmq.html'>Spider AP MQ</a>"
		."&nbsp;<img src='img/external.png'>"
		." command to align your particles to the selected templates. Multiprocessing additions has made this extremely fast (~1 hour)."
		."</p>\n";
	//echo "  <img src='img/align-rsm.png' width='125'><br/>\n";
	echo "</td></tr>\n";
}

if (!HIDE_IMAGIC && !HIDE_FEATURE) {
	/*
	** IMAGIC Reference Based Alignment
	*/

	echo "<tr><td width='100' align='center'>\n";
	echo "  <img src='img/imagic_logo.png' width='64'>\n";
	echo "</td><td>\n";
	echo "  <h3><a href='selectStackForm.php?expId=$expId&method=imagic'>IMAGIC Refinement</a></h3>\n";
	echo " <p> this method uses the "
		."<a href='http://www.imagescience.de/smi/index.htm'>IMAGIC m-r-a</a>"
		."&nbsp;<img src='img/external.png'>"
		." command to align your particles to the templates within a specified template stack"
		."</p>\n";
	echo "</td></tr>\n";
}


echo "</table>\n";
processing_footer();
exit;
