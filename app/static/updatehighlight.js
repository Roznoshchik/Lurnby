
var add_span;
var add;

function UpdateNewTopic(){

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
    input = byId('UpdateAddTopicInput')
    
    if (input.value === '' || input.value === ' ' || input.value === '  ')
    {
        input.classList.add('is-invalid')
        input.focus();
    }
    else 
    {   
            
        $.post('/topics/add/from_highlight', {
            title: input.value
        }).done(function(response) {
            add_span.innerHTML ='<button onclick ="UpdateNewTopic()" class="main-button save">Create new topic </button>';
            AddToTopic(response['id'], response['title'])
        }).fail(function() {
            add_span.innerHTML ='<div class="alert alert-danger alert-dismissible fade show" role="alert">There is already a topic with that title.<button onclick = "UpdateNewTopic()" type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button></div>'
        });
        
    }
  
};


    
function AddToTopic(id, title){
    
    var members, newLabel, newInput, newSpan

    members = byId('Members')
    newLabel = document.createElement('label')
    newInput = document.createElement('input')
    newSpan = document.createElement('span')

    newLabel.setAttribute('id', 'topic'+id)
    newLabel.classList.add('topic-label','upd-topic-label', 'btn', 'active', 'initialized')
    
    newInput.setAttribute('name', 'members')
    newInput.setAttribute('type', 'checkbox')
    newInput.checked = true
    newInput.setAttribute('value', title)
    newLabel.append(newInput)    
    members.append(newLabel)
    newSpan.innerText= title
    newLabel.appendChild(newSpan)


    newLabel.addEventListener('click', function(e){
        e=e || window.event;
        var target = e.target || e.srcElement;
        
        if (target.tagName === "LABEL"){

            console.log(target.firstElementChild.value)
            console.log(target.classList)
            target.classList.toggle('active')
            console.log(target.classList)

            /*
            var target = e.target
            if (target.classList.contains('active')){
                target.classList.remove('active')
            }
            else {
                target.classList.add('active')
            }
            */
        }
    });
}
  

function initialize_topics(){

    var all_topics = byClass('topic-label')
    
    for (var i=0; i< all_topics.length; i++){
        
        if (all_topics[i].classList.contains('initialized')){
            continue
        }
        else{
            all_topics[i].classList.add('initialized');
            all_topics[i].addEventListener("click", function(e){
                //console.log('click registered')
                e=e || window.event;
                var target = e.target || e.srcElement;
               
                //console.log(target.tagName)        

                
                if (target.tagName === "LABEL"){
                    /*
                    if (target.classList.contains('active')){
                        console.log('removing')
                        target.classList.remove('active')
                    }

                    else {
                        console.log('adding')
                        console.log(target.classList)
                        target.classList.add("active");
                        console.log(target.classList)
                    }
                    */
                    console.log(target.firstElementChild.value)
                    console.log(target.classList)
                    target.classList.toggle('active')
                    console.log(target.classList)
                }
            });
        }   
    }
}


function initialize_view_topics(){

    var all_topics = byClass('upd-topic-label')
    
    for (var i=0; i< all_topics.length; i++){
        
        if (all_topics[i].classList.contains('initialized')){
            continue
        }
        else{
            all_topics[i].classList.add('initialized');
            all_topics[i].addEventListener("click", function(e){
                //console.log('click registered')
                e=e || window.event;
                var target = e.target || e.srcElement;
               
                //console.log(target.tagName)        

                
                if (target.tagName === "LABEL"){
                    /*
                    if (target.classList.contains('active')){
                        console.log('removing')
                        target.classList.remove('active')
                    }

                    else {
                        console.log('adding')
                        console.log(target.classList)
                        target.classList.add("active");
                        console.log(target.classList)
                    }
                    */
                    console.log(target.firstElementChild.value)
                    console.log(target.classList)
                    target.classList.toggle('active')
                    console.log(target.classList)
                }
            });
        }
        
    }
}

    
function ViewHighlight(id){

    xhr = $.ajax(
                '/view_highlight/' + id).done(
                    function(data) {
                        json = JSON.parse(data)
                        
                        xhr = null
                        //$('#ViewHighlightModal').html(data);
                        byId('ViewHighlightModal').innerHTML = json['html'] 
                        add_span = byId('new-topic');
                        add = byId('add_new_tag');

                        initialize();
                        initialize_view_topics();
                        $('#ViewHighlightModal').modal('toggle')
                    }
    );

}

function clearHighlight(item){
    console.log('removing attributes!')  	
    item.removeAttribute('data-highlighted')
    item.removeAttribute('data-toggle')
    item.removeAttribute('data-html')
    item.removeAttribute('data-content')
    item.removeAttribute('data-timestamp')
    item.removeAttribute('data-container')
    item.removeAttribute('data-placement')
    item.removeAttribute('data-trigger')
    item.removeAttribute('id')
    item.removeAttribute('class')
    item.removeAttribute('tabindex')
    item.removeAttribute('title')
    item.removeAttribute('data-original-title')
  }

function ArchiveHighlight(id){
    if(byId(`highlight-${id}`)){
        byId(`highlight-${id}`).style.display = 'none'
        console.log('highlight hidden')
    
    url = 'archivehighlight/'+id
    $.get(url)
    .done(function(){
        byId('flashMessages').innerHTML=`
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
        <ul>
        <li>
            Highlight has been deleted. <button type="button" data-dismiss="alert" onclick="UnarchiveHighlight(${id})"class="main-button save cancel">UNDO</button>
        </li>
        </ul>
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
      `
    });

    }
    else{
        highlights = Array.from(byClass(`highlight${id}`))
        console.log(highlights)
        highlights.forEach(clearHighlight)
        url = `https://${window.location.host}/archivehighlight/${id}`
        $.get(url)

        var updated_content = byId('article_content').innerHTML
        $.post('/article/' + article_uuid + '/highlight-storage', {
          'updated_content': updated_content
        });




    }
    
    
    
}

function UnarchiveHighlight(id){
    byId(`highlight-${id}`).style.display = 'none'
    console.log('highlight hidden')
    
    url = 'unarchivehighlight/'+id
    $.get(url)
    .done(function(){
        byId(`highlight-${id}`).style.display = 'block'

        byId('flashMessages').innerHTML=`
        <div class="alert alert-success alert-dismissible fade show" role="alert">
        <ul>
        <li>
            Highlight has been unarchived.
        </li>
        </ul>
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
      `
    });
    
}




    
function UpdateHighlight(id){

    
    $('#ViewHighlightModal').modal('hide')
    
    
    
    var doc_tags,tags,untags, doc_topics, topics, untopics, notes, highlight, topicspace
    

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


    doc_topics = byClass('upd-topic-label')
    topics=[]
    untopics=[]

    for (var i = 0; i < doc_topics.length; i++){

        console.log(i)
        console.log(doc_topics[i].firstElementChild.value)
        console.log('\n')
        
        if (doc_topics[i].classList.contains('active')){
            topics.push(doc_topics[i].firstElementChild.value);
        }
        else {
            untopics.push(doc_topics[i].firstElementChild.value);
        }
    }

    var a_tags = byClass('active-tags')
    var a_topics = byClass('active-topics')
    
    atags = []
    atopics = []
    
    for (var i=0;i<a_tags.length;i++){
      atags.push(a_tags[i].firstElementChild.value)
    }
    
    for (var i=0;i<a_topics.length;i++){
      atopics.push(a_topics[i].firstElementChild.value)
    }
    
    topicspace = byId('topics_all')
    if (topicspace){
        data = {
            'notes': notes,
            'highlight':highlight,
            'topics':topics,
            'untopics':untopics,
            // 'tags':tags,
            // 'untags':untags,
            // 'atags':atags,
            'atopics':atopics,
            'topics-page':'true',
            'do_not_review': byId('do_not_review').checked

        }
    }
    else {
        data = {
            'notes': notes,
            'highlight':highlight,
            'topics':topics,
            'untopics':untopics,
            // 'tags':tags,
            // 'untags':untags,
            // 'atags':false,
            'atopics':false,
            'topics-page':'false',
            'do_not_review': byId('do_not_review').checked
        }
    }
    
    data = JSON.stringify(data)
    console.log(data)
       
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
            console.log(data)
        }

        if (typeof apply_filters === "function") { 
            console.log('apply filters exists')
            apply_filters()
        }
        
    }); 

}

