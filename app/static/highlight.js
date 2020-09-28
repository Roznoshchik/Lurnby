
var infodiv = document.getElementById('infoDiv');
var selectedText;
var content = document.getElementById('content');

var activeRange;
var selectedObj;
var position;

/*
function textActions(event) {
  selectedObj = window.getSelection();
 
 if (selectedObj.rangeCount > 0){
    selectedText = selectedObj.getRangeAt(0);
 }

if (selectedText != "") {
 
 $('#infoDiv').css('display', 'block');
 $('#infoDiv').css('position', 'absolute');
 $('#infoDiv').css('left', event.pageX);
 $('#infoDiv').css('top', event.pageY);
 //infodiv.style.visibility = 'visible';
}

else{
      infodiv.style.display = 'none';

}

}
*/

//test code

function textActions(event) {

  
  var h = document.documentElement, 
  b = document.body,
  st = 'scrollTop',
  sh = 'scrollHeight';
  
  position =  (h[st] || b[st]) / (h[sh] || b[sh]) * 100;



  selectedObj = window.getSelection();
 
  var x = selectedObj.toString().length

  if ( x > 5 ) {
    selectedText = selectedObj.getRangeAt(0);


    console.log(selectedText)
    
    var rect = selectedText.getBoundingClientRect();
    
    var width = (window.innerWidth || document.documentElement.clientWidth)
    
    $('#infoDiv').css('display', 'block');
    $('#infoDiv').css('position', 'fixed');

    if ((rect['right'] + 130) <= width ){
      $('#infoDiv').css('bottom', rect['bottom']);
      $('#infoDiv').css('left', (rect['right'] + 8));
    }     
    
    else {
      $('#infoDiv').css('top', (rect['bottom'] + 8));
      $('#infoDiv').css('left', rect['left']);
    }
  }
  else{
        infodiv.style.display = 'none';

  }

}



//test code end



$(function () {
    $('[data-toggle="popover"]').popover()
  })



content.addEventListener("mouseup", textActions);
content.addEventListener("touchend", textActions);
content.addEventListener("keyup", textActions);

//content.addEventListener('selectionchange', textActions);



$('#addhighlight').click(function(){
    
    document.getElementById('infoDiv').style.display = 'none';
    

}); 

$('#AddHighlightModal').on('show.bs.modal', function (event) {
    var button = $(event.relatedTarget) // Button that triggered the modal
    var rawhighlight = selectedText // selected text
    var highlight_position = position; 
    // If necessary, you could initiate an AJAX request here (and then do the updating in a callback).
    // Update the modal's content. We'll use jQuery here, but you could use a data binding library or other methods instead.
    $('#HighlightField').val(rawhighlight);
    $('#highlight_position').val(highlight_position);


  })

function showaddhighlightmodal(){
    $('#AddHighlightModal').modal('show')
  }