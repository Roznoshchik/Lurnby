// this is from https://stackoverflow.com/questions/304837/javascript-user-selection-highlighting
function getSafeRanges(dangerous) {
    var a = dangerous.commonAncestorContainer;
    // Starts -- Work inward from the start, selecting the largest safe range
    var s = new Array(0), rs = new Array(0);
    if (dangerous.startContainer != a)
        for(var i = dangerous.startContainer; i != a; i = i.parentNode)
            s.push(i)
    ;
    if (0 < s.length) for(var i = 0; i < s.length; i++) {
        var xs = document.createRange();
        if (i) {
            xs.setStartAfter(s[i-1]);
            xs.setEndAfter(s[i].lastChild);
        }
        else {
            xs.setStart(s[i], dangerous.startOffset);
            xs.setEndAfter(
                (s[i].nodeType == Node.TEXT_NODE)
                ? s[i] : s[i].lastChild
            );
        }
        rs.push(xs);
    }

    // Ends -- basically the same code reversed
    var e = new Array(0), re = new Array(0);
    if (dangerous.endContainer != a)
        for(var i = dangerous.endContainer; i != a; i = i.parentNode)
            e.push(i)
    ;
    if (0 < e.length) for(var i = 0; i < e.length; i++) {
        var xe = document.createRange();
        if (i) {
            xe.setStartBefore(e[i].firstChild);
            xe.setEndBefore(e[i-1]);
        }
        else {
            xe.setStartBefore(
                (e[i].nodeType == Node.TEXT_NODE)
                ? e[i] : e[i].firstChild
            );
            xe.setEnd(e[i], dangerous.endOffset);
        }
        re.unshift(xe);
    }

    // Middle -- the uncaptured middle
    if ((0 < s.length) && (0 < e.length)) {
        var xm = document.createRange();
        xm.setStartAfter(s[s.length - 1]);
        xm.setEndBefore(e[e.length - 1]);
    }
    else {
        return [dangerous];
    }

    // Concat
    rs.push(xm);
    response = rs.concat(re);    

    // Send to Console
    return response;
}


function highlightSelection() {
    var userSelection = window.getSelection().getRangeAt(0);
    var safeRanges = getSafeRanges(userSelection);
    for (var i = 0; i < safeRanges.length; i++) {
        highlightRange(safeRanges[i]);
    }
}


function highlightRange(range) {
    var newNode = document.createElement("span");
    newNode.setAttribute(
       "style",
       "background-color: yellow; display: inline; border: none;"
    );

    newNode.setAttribute('type','button' );

    newNode.setAttribute('class','button-inline TEMP' );

    newNode.setAttribute('data-toggle','popover' );
    newNode.setAttribute('data-container','body' );
    newNode.setAttribute('data-placement','right' );
    newNode.setAttribute('data-trigger','focus' );
    newNode.setAttribute('title','OPTIONS' );
    newNode.setAttribute('data-content','This will offer some options for what to do with a past highlight.' );

    range.surroundContents(newNode);
}


// these are my triggers


var infodiv = document.getElementById('infoDiv');
var selectedText;
var content = document.getElementById('content');
function textActions() {
 var selectedObj = window.getSelection();

 selectedText = selectedObj.getRangeAt(0);

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
content.addEventListener("keyup", textActions);



$('#addhighlight').click(function(){
  highlightSelection();
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