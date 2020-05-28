var selectedText;
function textActions() {
     var selectedObj = window.getSelection();
 
     selectedText = selectedObj.getRangeAt(0);
 
   if (selectedText != "") {
     
     $('#infoDiv').css('display', 'block');
     $('#infoDiv').css('position', 'absolute');
     $('#infoDiv').css('left', event.pageX);
     $('#infoDiv').css('top', event.pageY);
   }
   
 }
   

 
 document.addEventListener("mouseup", textActions);
 document.addEventListener("keyup", textActions);
 document.addEventListener("click", function(){
     if( $('#infodiv').css('display') == 'block') ){
        $('#infodiv').css('display', 'none')
     }
 })






 
 $('#addcomment').click(function(){
   $('#infoDiv').css('display', 'none');
   var text = '<h4>Add following text to comment function:</h4>' + selectedText;
   bootbox.alert(text);  
   
 });
 
 $('#addtolist').click(function(){
   $('#infoDiv').css('display', 'none');
   var text = '<h4>Add following text to some list that will be searchable </h4>' + selectedText;
   bootbox.alert(text);
 });
       
 
   
 
 document.addEventListener("mouseup", textActions);
 document.addEventListener("keyup", textActions);
 
 
 