
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

function sendForm(name, pID) {
    jsfexp=document.listform.allfile.options[document.
    listform.allfile.selectedIndex].value;
    document.listform.action = name+"?"+pID+"="+jsprefId;
    return true;
}

function getdata()
{
	if(vtree==true) {
		jsfexp=	document.listform.allfile.options[document.
			listform.allfile.selectedIndex].value;
		var treeif = document.getElementById('treeiframe');
		var memonodes = parent.infomv.openNodes;
		treeif.src = 'getdata.php?id='+escape(jsfexp)+'&table='+escape(jstmv)+'&session='+escape(jsexpId)+'&r='+memonodes;
	}
}

function newexp()
{
    document.listform.submit(); 
}

function zoom(val) {
	parent.picturebox.document.getElementById('imgmv').width = (jsimgwidth*val/100);
	parent.picturebox.document.getElementById('imgmv').height = (jsimgheight*val/100);
}

function updateGradient() {
  	document.getElementById('gradientDiv').style.background = 'url('+jsbaseurl+'img/dfe/grad.php?min='+jsminpix+'&max='+jsmaxpix+')'; 

}

function newscale(){
	setQuality();
	setSize();
	newimg = new Image();
	newimg.src= jsbaseurl+jsimgmv+"?table="+escape(jstmv)+"&session="+escape(jsexpId)+"&id="+escape(jsfexp)+"&t="+jsquality+"&s="+jssize+"&np="+jsminpix+"&xp="+jsmaxpix; 
	img_timer=setInterval('imgIsComplete()',25);	
}

function imgIsComplete() {
	if (newimg.complete) {
		clearInterval(img_timer)
		parent.picturebox.document.getElementById('imgmv').src = newimg.src;
		jsimgwidth = newimg.width;
		jsimgheight = newimg.height;
		zoom(jszoom);
	}
} 

function setQuality(){
	var jsind;
	if (document.listform.l_quality.length !=0) {
		jsind=document.listform.l_quality.options.selectedIndex;
        	jsquality=document.listform.l_quality.options[jsind].value
	}
}

function setSize(){
	var jsind;
	if (document.listform.l_size.length !=0) {
		jsind=document.listform.l_size.options.selectedIndex;
        	jssize=document.listform.l_size.options[jsind].value
	}
}

function setlist(){
	if (jsmvId.length != 0){
		var selm=document.listform.mlist.options[document.listform.mlist.selectedIndex].value;
		window.document.listform.mvsel.value=selm;
	} if (jsv2Id.length != 0){
		var sel2=document.listform.v2list.options[document.listform.v2list.selectedIndex].value;
		window.document.listform.v2sel.value=sel2;
	} if (jsv1Id.length != 0){
		var sel1=document.listform.v1list.options[document.listform.v1list.selectedIndex].value;
		window.document.listform.v1sel.value=sel1;
	}
}

function newfile() { 
     setQuality();
     currentfile=document.listform.allfile.options[document.
     listform.allfile.selectedIndex].text
     window.document.listform.filename_text.value=currentfile; 
     jsfexp=document.listform.allfile.options[document.
     listform.allfile.selectedIndex].value
	var lId;
	if (jsmvId.length != 0){
		parent.picturebox.document.getElementById('imgmv').src=jsimgmv+"?table="+escape(jstmv)+"&session="+escape(jsexpId)+"&id="+escape(jsfexp)+"&t="+jsquality+"&s="+jssize+"&np="+jsminpix+"&xp="+jsmaxpix; 
		// var imgURL="getimage.php?tmpl="+jsimgmv+"&table="+escape(jstmv)+"&session="+escape(jsexpId)+"&id="+escape(jsfexp)+"&t="+jsquality+"&s="+jssize+"&np="+jsminpix+"&xp="+jsmaxpix; 
		// picturebox.document.location.replace(imgURL);
		
//		lId=GetLinkId('Lmv');
//		if ((lId=GetLinkId('Lmv')) != -1 ) {
//		url = "nwi.php?Lmv&r=1&s=1&table="+escape(jstmv);
//		document.links[lId].href="javascript:popUp('"+url+"')"; 
		// }
	}
	var URL="getpreset.php?id="+escape(jsfexp);
	ifpmv.document.location.replace(URL);
}

function bsSliderChange1(sliderObj, val, newPos){ 
  jsminpix = val;
  updateGradient();
}

function bsSliderChange2(sliderObj, val, newPos){ 
  jsmaxpix = val;
  updateGradient();
}

function bsSliderChange4(sliderObj, val, newPos){ 
  jszoom= val;
  zoom(val);
}

function ir() {
        if (ns4) {parent.picturebox.document.captureEvents(Event.MOUSEMOVE);}
	window.onresize=getIframesize;
        parent.picturebox.document.newimgmv.onmousemove=mousemove;
        parent.picturebox.document.newimgmv.onmousedown=mousedown;
        parent.picturebox.document.newimgmv.onmouseup=mouseup;
	getIframesize();
}

function getIframesize(){
	var iframewidth = ie ? parent.picturebox.document.body.clientWidth : parent.picturebox.innerWidth;
	var iframeheight = ie ? parent.picturebox.document.body.clientHeight : parent.picturebox.innerHeight;
	cx=parseInt(iframewidth/2);
	cy=parseInt(iframeheight/2);
}

function mousedown(e){
	mousecoord(e);
}

function mouseup(){
	if (ns6) {
		h = parent.picturebox.pageXOffset; 
		w = parent.picturebox.pageYOffset;
		initx=h;
		inity=w;
	}
	parent.picturebox.scrollBy(mx-initx-cx,my-inity-cy);
}

function mousemove(e) {
	mousecoord(e);
	offsetx=0;
	offsety=0;
        if (ie) {
		offsetx=parent.picturebox.document.body.scrollLeft;
		offsety=parent.picturebox.document.body.scrollTop
	}
	coordx = parseInt((mx+offsetx)/jszoom*100);
	coordy = parseInt((my+offsety)/jszoom*100);
	document.listform.tq.value=coordx+","+coordy;
}

function mousecoord(e) {
        if (ns4||ns6) {var mouseX=e.pageX; var mouseY=e.pageY}
        if (ie) {var mouseX=parent.picturebox.event.x; var mouseY=parent.picturebox.event.y}
	mx = mouseX;
	my = mouseY;
}

function updateratiomap() {
	ratiomap=jssize/jsmapsize;
}

function mapmousecoord(e) {
	updateratiomap();
	var deoffsetx=0;
	var deoffsety=0;
	var mapmxo = parseInt(crossobj.style.left);
	var mapmyo = parseInt(crossobj.style.top);
	if (ns6) {
		var mapmouseX=e.clientX;
		var mapmouseY=e.clientY
		initx = parent.picturebox.pageXOffset; 
		inity = parent.picturebox.pageYOffset;
	}
	if (ie) {
		var mapmouseX=event.x;
		var mapmouseY=event.y
		var deoffsetx=parent.picturebox.document.body.scrollLeft;
		var deoffsety=parent.picturebox.document.body.scrollTop
	}
	mapmx = parseInt((mapmouseX-mapmxo-imgmapoffsetx)*ratiomap/100*jszoom);
	mapmy = parseInt((mapmouseY-mapmyo-imgmapoffsety)*ratiomap/100*jszoom);
//	alert("mapmo"+mapmxo+" "+mapmyo+"\n"+"mapmmouse"+mapmouseX+" "+mapmouseY+"\n"+"mapm "+mapmx+", "+mapmy+" iniit "+initx+", "+inity+ " ratio "+ratiomap+"\n center"+cx+", "+cy +" \n off: "+deoffsetx+", "+deoffsety);
	parent.picturebox.scrollBy(mapmx-initx-cx-deoffsetx,mapmy-inity-cy-deoffsety);
}

function initmap() {
	if (ie||ns6){
        	if (ie) {
			imgmapoffsetx +=1;
			imgmapoffsety +=5;
		}

		viewlink=document.getElementById("viewlink");

		crossobj=document.getElementById? document.getElementById("imagemap") : document.all.imagemap
		crossobj.style.left=750;
		crossobj.style.top=50;
		crossobj.innerHTML='<table border=0 width=256><tr><td><div align=left><b onClick=updatemap()>refresh</b></div></td><td><div align=right id=divstyle><b onClick=closemappreview()>close</b></div></td></tr></table><img id="mapimg" name="mapimgname" width=256 height=256 >'
		mapimg = document.getElementById('mapimg');
		updatemap();
        	document.mapimgname.onmousedown=mapmousecoord;
	}
}

function inittree() {
	if (ie||ns6){

		viewtreelink=document.getElementById("viewtreelink");
		treedata=document.getElementById? document.getElementById("treedata") : document.all.treedata
		treedata.style.left=750;
		treedata.style.top=327;
		treedata.innerHTML='<table border=0 width=256><tr><td><div align=left><b onClick=getdata()>refresh</b></div></td><td><div align=right id=divstyle><b onClick=closetreepreview()>close</b></div></td></tr></table><iframe class=textarea id=treeiframe name="infomv" src="getdata.php" frameborder="0" width=256 height=400 marginheight="1" marginwidth="5" scrolling="yes"></iframe>'
		getdata();
	}
}

function updatemap(){
	if (vmap==true)
		mapimg.src= jsbaseurl+jsimgmv+"?table="+escape(jstmv)+"&session="+escape(jsexpId)+"&id="+escape(jsfexp)+"&t=80&s=512&np="+jsminpix+"&xp="+jsmaxpix; 
}

function viewtreediv() {
	if(treedata.style.visibility=="visible") {
		treedata.style.visibility="hidden";
		viewtreelink.childNodes[0].nodeValue=viewstr+"tree";
		vtree=false;
	} else {
		vtree=true;
		treedata.style.visibility="visible";
		viewtreelink.childNodes[0].nodeValue=hidestr+"tree";
	}
}


function viewmap() {
	if(crossobj.style.visibility=="visible") {
		crossobj.style.visibility="hidden";
		viewlink.childNodes[0].nodeValue=viewstr+"map";
		vmap=false;
	} else {
		vmap=true;
		crossobj.style.visibility="visible";
		viewlink.childNodes[0].nodeValue=hidestr+"map";
	}
}

function closemappreview(){
	crossobj.style.visibility="hidden"
	viewlink.childNodes[0].nodeValue=viewstr+"map";
}

function closetreepreview(){
	treedata.style.visibility="hidden";
	viewtreelink.childNodes[0].nodeValue=viewstr+"tree";
}


function incIndex(){
 if (document.listform.allfile.length !=0) {
     for (var i = 0; i < document.listform.allfile.length; i++) {
      if (document.listform.allfile.options[i].selected == true) {
       index=i  
      } 
     }
     if (index == document.listform.allfile.length - 1) {
 	index = index-1
     }	
     document.listform.allfile.options[index+1].selected=true;
 }
}


function decIndex(){
 if (document.listform.allfile.length !=0) {
     for (var i = 0; i < document.listform.allfile.length; i++) {
      if (document.listform.allfile.options[i].selected == true) {
       index=i  
      } 
     }
     if (index == 0) {
 	index = index+1
     }	
     document.listform.allfile.options[(index-1)].selected=true;
 }
}
