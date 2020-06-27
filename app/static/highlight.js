
var infodiv = document.getElementById('infoDiv');
var selectedText;
var content = document.getElementById('content');

var activeRange;
var selectedObj;

function textActions() {
 selectedObj = window.getSelection();
 
 if (selectedObj.rangeCount > 0){
    selectedText = selectedObj.getRangeAt(0);
 }

if (selectedText != "") {
 
 $('#infoDiv').css('display', 'block');
 $('#infoDiv').css('position', 'absolute');
 $('#infoDiv').css('left', event.pageX);
 $('#infoDiv').css('top', event.pageY);
 infodiv.style.visibility = 'visible';
}

else{
      infodiv.style.visibility = 'hidden';

}

}

$(function () {
    $('[data-toggle="popover"]').popover()
  })



content.addEventListener("mouseup", textActions);
content.addEventListener("touchend", textActions);
content.addEventListener("keyup", textActions);



$('#addhighlight').click(function(){
    
    document.getElementById('infoDiv').style.visibility = 'hidden';
    

}); 

$('#AddHighlightModal').on('show.bs.modal', function (event) {
    var button = $(event.relatedTarget) // Button that triggered the modal
    var rawhighlight = selectedText // selected text
    // If necessary, you could initiate an AJAX request here (and then do the updating in a callback).
    // Update the modal's content. We'll use jQuery here, but you could use a data binding library or other methods instead.
    $('#HighlightField').val(rawhighlight)
  })

function showaddhighlightmodal(){
    $('#AddHighlightModal').modal('show')
  }