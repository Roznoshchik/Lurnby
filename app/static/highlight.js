
var infodiv = document.getElementById('infoDiv');
var selectedText;
var content = document.getElementById('content');

var activeRange;
var selectedObj;
var position;


function textActions(event) {

  // var h = document.documentElement, 
  // b = document.body,
  // st = 'scrollTop',
  // sh = 'scrollHeight';
  
  // position =  (h[st] || b[st]) / (h[sh] || b[sh]) * 100;

  let docElem = document.documentElement,
      docBody = document.body,
      scrollTop = docElem['scrollTop'] || docBody['scrollTop'],
      scrollBottom = (docElem['scrollHeight'] || docBody['scrollHeight']) - window.innerHeight,
      scrollPercent = scrollTop / scrollBottom;

      position =  scrollPercent * 100;




      selectedObj = window.getSelection();
      highlightText = window.getSelection().toString();
 
  var x = selectedObj.toString().length

  if ( x > 5 ) {
    selectedText = selectedObj.getRangeAt(0);


    //console.log(selectedText)
    
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




$(function () {
    $('[data-toggle="popover"]').popover()
  })



content.addEventListener("mouseup", textActions);
content.addEventListener("touchend", textActions);
content.addEventListener("keyup", textActions);

//content.addEventListener('selectionchange', textActions);



$('#addhighlight').click(function(){
    
    document.getElementById('infoDiv').style.display = 'none';
    //initialize_topics();

}); 

$('#AddHighlightModal').on('show.bs.modal', function (event) {
    var button = $(event.relatedTarget) // Button that triggered the modal
    //var rawhighlight = selectedObj.toString() // selected text
    var rawhighlight = highlightText;

    selectedObj.removeAllRanges();

    var highlight_position = position; 
    // If necessary, you could initiate an AJAX request here (and then do the updating in a callback).
    // Update the modal's content. We'll use jQuery here, but you could use a data binding library or other methods instead.
    //$('#HighlightField').val(rawhighlight);
    byId('HighlightField').value = rawhighlight
    tinymce.EditorManager.execCommand('mceSetContent',rawhighlight, 'HighlightField');



    byId('highlight_position').value = highlight_position
    //$('#highlight_position').val(highlight_position);
    byId('message-text').value='';
    var add_highlight_nonmember_list = Array.from(topics)
    autocomplete(byId("new_highlight_topic_input"), add_highlight_nonmember_list, byId('NewHighlightMembers'), create=true, 'addhighlight');

    // var active = byClass('active')
    //   for (var i = active.length - 1; i>=0; i--){
    //     active[i].classList.remove('active')
    //     console.log('removed')
    //   }

  })

function showaddhighlightmodal(){
  tinymce.EditorManager.execCommand('mceRemoveEditor',true, 'HighlightField');
  tinymce.EditorManager.execCommand('mceRemoveEditor',true, 'message-text');

  tinymce.EditorManager.init({
    selector: '#HighlightField',
    menubar: 'insert format',
    resize: 'vertical',
    toolbar: 'styleselect | bold italic underline | hr',
    skin: darkModeOn() ? "oxide-dark":"oxide",
    content_css: darkModeOn() ? "dark": "light",
    plugins: 'link hr', 
    mobile: {
        height:300
    }
  });

  tinymce.EditorManager.init({
    selector: '#message-text',
    menubar: 'insert format',
    resize: 'vertical',
    toolbar: 'styleselect | bold italic underline | hr',
    skin: darkModeOn() ? "oxide-dark":"oxide",
    content_css: darkModeOn() ? "dark": "light",
    plugins: 'link hr', 
    mobile: {
        height:300
    }
  });


  //initialize_topics();
  $('#AddHighlightModal').modal('show');
  
}