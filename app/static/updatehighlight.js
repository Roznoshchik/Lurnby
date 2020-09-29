
var add_span;
var add;

function UpdateNewTopic(){

    
    //$('#Update-CreateTopic').html('<div class = "form-row align-items-center"> <div class="col-sm-6 my-1"> <input autofocus="" class="form-control" id="UpdateAddTopicInput" name="title" placeholder="Topic title..." required="" type="text" value=""></input></div> <div class="col-auto my-1"> <button type="button" onclick="UpdateCancelNewTopic()" class="main-button cancel">cancel</button> </div>  <div class="col-auto my-1"> <button onclick="UpdateNewTopicSubmit()" type="button" class="main-button save">add</button> </div> </div> ');
    //$('#UpdateAddTopicInput').trigger('focus');
    
    add_span.innerHTML = `
            <div class="form-row align-items-center">
                <div class="col-auto">
                    <label class="sr-only" for="inlineFormInput">Name</label>
                    <input id = "UpdateAddTopicInput" name = title" type="text" class="form-control mb-2" id="inlineFormInput" placeholder="Topic title" required>
                    <input disabled style="display: none" aria-hidden="true"></input>

                </div>
                <div class="col-auto">
                    <button id = "submit_new_tag" type="button" onclick = "UpdateNewTopicSubmit()" class="main-button add-new">Add</button>
                    <button type="button" class="btn cancel mb-2" onclick="UpdateCancelNewTopic()">Cancel</button>
                </div>
            </div>
    `;

    var input = byId('UpdateAddTopicInput');
    input.focus();


  };

  function UpdateCancelNewTopic(){
      add_span.innerHTML ='<button onclick ="UpdateNewTopic()" class="main-button save">Create new topic </button>';
  };


  function UpdateNewTopicSubmit(){
    $.post('/topics/add', {
        


      title: $('#UpdateAddTopicInput').val()
    }).done(function(response) {
        add_span.innerHTML ='<button onclick ="UpdateNewTopic()" class="main-button save">Create new topic </button>';
        AddToTopic(response['id'], response['title'])
    }).fail(function() {
        add_span.innerHTML ='<div class="alert alert-danger alert-dismissible fade show" role="alert">There is already a topic with that title.<button onclick = "UpdateNewTopic()" type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button></div>'
    });
};







function RemoveFromTopic(id, title){
    //newId = '"' + id + '"'
    //newTitle = '"' + title + '"'
    
    newId = `"${id}"`
    newTitle = `"${title}"`   
    var nonmembers = document.getElementById('NonMembers')
    var removeMember = document.getElementById(id)
    var newLabel = document.createElement('label')
    newLabel.setAttribute('id', id)
    newLabel.classList.add('topic-label', 'btn')
    newLabel.setAttribute('onclick', `AddToTopic(${newId}, ${newTitle})`)
    var newSpan = document.createElement('span')
    newSpan.innerHTML = '<input name = "nonmembers" type="checkbox" checked value="' + title + '">' + title
    newLabel.append(newSpan)
    nonmembers.append(newLabel)
    removeMember.parentNode.removeChild(removeMember);
}
    
    
function AddToTopic(id, title){
    newId = '"' + id + '"'
    newTitle = '"' + title + '"'

    var members = byId('Members')
    var removeMember = byId(id)

    var newLabel = document.createElement('label')
    newLabel.setAttribute('id', id)
    newLabel.classList.add('topic-label', 'btn', 'active')
    newLabel.setAttribute('onclick', 'RemoveFromTopic(' + newId + ',' + newTitle + ')')
    
    var newSpan = document.createElement('span')

    newSpan.innerHTML = '<input name = "members" type="checkbox" checked value="' + title + '">' + title 

    newLabel.append(newSpan)
    members.append(newLabel)
    
    removeMember.parentNode.removeChild(removeMember);

}
    
    
    
    
function ViewHighlight(id){


    xhr = $.ajax(
                '/view_highlight/' + id).done(
                    function(data) {
                        xhr = null
                        $('#ViewHighlightModal').html(data);
                        add_span = byId('new-topic');
                        add = byId('add_new_tag');
                        initialize();
                        $('#ViewHighlightModal').modal('toggle')
                    }
    );
        
   
            
   
    
  
    
    

}
    
    
    
function UpdateHighlight(id){

    $('#ViewHighlightModal').modal('hide')
    var doc_tags,tags,untags, doc_topics, topics, doc_untopics, untopics, notes, highlight
    
    notes = byId('message-text').value
    highlight = byId('HighlightField').value
    
    doc_tags= byClass('update-highlight')
    tags=[]
    untags=[]
    for (var i = 0; i <doc_tags.length; i++){
        if(doc_tags[i].classList.contains('tagged')){
            tags.push(doc_tags[i].firstElementChild.value);
        }
        else {
            untags.push(doc_tags[i].firstElementChild.value);
        }
    }


    doc_topics = document.getElementsByName('members')
    doc_untopics = document.getElementsByName('nonmembers')
    topics=[]
    untopics=[]

    for (var i = 0; i <doc_topics.length; i++){
        topics.push(doc_topics[i].value);
    }

    for (var i = 0; i <doc_untopics.length; i++){
        untopics.push(doc_untopics[i].value);
    }

    data = {
        'notes': notes,
        'highlight':highlight,
        'topics':topics,
        'untopics':untopics,
        'tags':tags,
        'untags':untags
    }

    data = JSON.stringify(data)
    url = '/view_highlight/' + id

    $.post(url, {
        'data':data
    }).done(function( data ) {
        console.log(data)
    }); 




    console.log(data)



    /*
    $("#UpdateHighlightForm").ajaxSubmit({
        url: '/view_highlight/' + id, 
        type: 'post',
        success: function(){
            //check if url contains topics and only then reloads
            //this is because i use this same script on the text.html page and no reload is necessary. 
            if (window.location.href.indexOf("topics") > -1) {
                location.reload();
                return false;
              }
             
        },
        //error: function(){ FailedToAddHighlight() }
    });
    */    

}

