
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



/*
function RemoveFromTopic(id, title){
    //newId = '"' + id + '"'
    //newTitle = '"' + title + '"'
    
    //newId = `"${id}"`
    //newTitle = `"${title}"`   
    var nonmembers = byId('NonMembers')
    var removeMember = byId(id)

    var newLabel = document.createElement('label')
    newLabel.setAttribute('id', id)
    newLabel.classList.add('topic-label', 'btn')
    newLabel.setAttribute('onclick', `AddToTopic("${id}", "${title}")`)
    
    var newSpan = document.createElement('span')
    newSpan.innerHTML = '<input name = "nonmembers" type="checkbox" checked value="' + title + '">' + title
    newLabel.append(newSpan)
    
    nonmembers.append(newLabel)
    removeMember.parentNode.removeChild(removeMember);
}
    
    
function AddToTopic(id, title){
    //newId = `"${id}"`
    //newTitle = `"${title}"` 

    var members = byId('Members')
    var removeMember = byId(id)

    var newLabel = document.createElement('label')
    newLabel.setAttribute('id', id)
    newLabel.classList.add('topic-label', 'btn', 'active')
    newLabel.setAttribute('onclick', `RemoveFromTopic("${id}", "${title}")`)
    
    var newSpan = document.createElement('span')
    newSpan.innerHTML = '<input name = "members" type="checkbox" checked value="' + title + '">' + title 
    newLabel.append(newSpan)
    
    members.append(newLabel)
    removeMember.parentNode.removeChild(removeMember);
}
    
*/

function initialize_topics(){
    var all_topics = byClass('topic-label')
    for (var i=0; i< all_topics.length; i++){
        all_topics[i].addEventListener("click", function(e){
            e=e || window.event;
            var target = e.target || e.srcElement;
           
            if (target.tagName === "LABEL"){
                var target = e.target
                if (target.classList.contains('active')){
                    target.classList.remove('active')
                }
                else {
                    target.classList.add('active')
                }
            }
        });
    }
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
                        initialize_topics();
                        $('#ViewHighlightModal').modal('toggle')
                    }
    );
        
   
            
   
    
  
    
    

}
    
    
    
function UpdateHighlight(id){
    $('#ViewHighlightModal').modal('hide')

    
    var doc_tags,tags,untags, doc_topics, topics, doc_untopics, untopics, notes, highlight, topicspace
    

    notes = byId('view_highlight_notes').value
    highlight = byId('view_highlight_text').value
    
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


    doc_topics = byClass('topic-label')
    topics=[]
    untopics=[]

    for (var i = 0; i <doc_topics.length; i++){
        if (doc_topics[i].classList.contains('active')){
            topics.push(doc_topics[i].firstElementChild.value);
        }
        else {
            untopics.push(doc_topics[i].firstElementChild.value);
        }
    }

   

    topicspace = byId('topics_all')
    if (topicspace){
        data = {
            'notes': notes,
            'highlight':highlight,
            'topics':topics,
            'untopics':untopics,
            'tags':tags,
            'untags':untags,
            'topics-page':'true'
        }
    }
    else {
        data = {
            'notes': notes,
            'highlight':highlight,
            'topics':topics,
            'untopics':untopics,
            'tags':tags,
            'untags':untags,
            'topics-page':'false'
        }
    }
    
    data = JSON.stringify(data)
    url = '/view_highlight/' + id

    topicspace = byId('topics_all')
        if (topicspace){
            topicspace.innerHTML=`
                <div class = "loading">
                    <p>Loading...</p>
                    <svg xmlns="http://www.w3.org/2000/svg" style="margin:auto;background:0 0" width="64" height="64" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid" display="block"><circle cx="50" cy="50" fill="none" stroke="#e3e3e3" stroke-width="5" r="32" stroke-dasharray="150.79644737231007 52.26548245743669" transform="rotate(144.01 50 50)"><animateTransform attributeName="transform" type="rotate" repeatCount="indefinite" dur="1s" values="0 50 50;360 50 50" keyTimes="0;1"/></circle></svg>
                </div>
            `
        }

        
    $.post(url, {
        'data':data
    }).done(function( data ) {
        if (topicspace){
            topicspace.innerHTML = data;
            initialize();
        }
        
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

