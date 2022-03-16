
var add_span;
var add;
var nonmember_list;


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
            
        $.post('/app/topics/add/from_highlight', {
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

    var all_topics = Array.from(byClass('member'))

    console.log(all_topics)
    all_topics.forEach( topic => topic.addEventListener("click", function(e){
        e=e || window.event;
        var target = e.target || e.srcElement;
        byId(target.id).remove()
        nonmember_list.push(topic.innerText)

    }))


    // for (var i=0; i< all_topics.length; i++){
    //     title = all_topics[i].innerText
    //     all_topics[i].addEventListener("click", function(e){
    //         e=e || window.event;
    //         var target = e.target || e.srcElement;
    //         byId(target.id).remove()
    //         nonmember_list.push(title)
    //     })
        
    //     if (all_topics[i].classList.contains('initialized')){
    //         continue
    //     }
    //     else{
    //         all_topics[i].classList.add('initialized');
    //         all_topics[i].addEventListener("click", function(e){
    //             //console.log('click registered')
    //             e=e || window.event;
    //             var target = e.target || e.srcElement;
               
    //             //console.log(target.tagName)        

                
    //             if (target.tagName === "LABEL"){
    //                 /*
    //                 if (target.classList.contains('active')){
    //                     console.log('removing')
    //                     target.classList.remove('active')
    //                 }

    //                 else {
    //                     console.log('adding')
    //                     console.log(target.classList)
    //                     target.classList.add("active");
    //                     console.log(target.classList)
    //                 }
    //                 */
    //                 console.log(target.firstElementChild.value)
    //                 console.log(target.classList)
    //                 target.classList.toggle('active')
    //                 console.log(target.classList)
    //             }
    //         });
    //     }
        
    // }
}

    
function ViewHighlight(id){
    url = '/app/view_highlight/' + id
    fetch(url)
    .then(response => response.json())
    .then(data => {
        $('#ViewHighlightModal').html(data['html']);
        nonmember_list = data['nonmember_list'];
        console.log(nonmember_list)
        add_span = byId('new-topic');
        add = byId('add_new_tag');
        initialize();
        initialize_view_topics();
        autocomplete(byId("topic_input"), nonmember_list, byId('Members'), create=true, 'viewhighlight');

        let existingNotes = byId('view_highlight_notes').value
        let existingHighlight = byId('view_highlight_text').value

        tinymce.EditorManager.execCommand('mceRemoveEditor',true, 'view_highlight_notes');
        tinymce.EditorManager.execCommand('mceRemoveEditor',true, 'view_highlight_text');

        
        tinymce.EditorManager.init({
            selector: '#view_highlight_text',
            menubar: 'insert format',
            resize: 'vertical',
            toolbar: 'styleselect | bold italic underline | numlist bullist | hr | image | code',
            skin: darkModeOn() ? "oxide-dark":"oxide",
            content_css: darkModeOn() ? "dark": "light",
            plugins: 'image imagetools lists code link hr', 
            // image_dimensions: false,
            object_resizing : true,
            image_class_list: [
              {title: 'Width100', value: 'image100'},
            ],
            mobile: {
                height:300
            },
            setup: function (editor) {
                editor.on('init', function (e) {
                  editor.setContent(`${existingHighlight}`);
                });
             }
            
            
        });

        tinymce.EditorManager.init({
            selector: '#view_highlight_notes',
            menubar: 'insert format',
            resize: 'vertical',
            toolbar: 'styleselect | bold italic underline | numlist bullist | hr | image | code',
            skin: darkModeOn() ? "oxide-dark":"oxide",
            content_css: darkModeOn() ? "dark": "light",
            plugins: 'image imagetools lists code link hr',
            // image_dimensions: false,
            object_resizing : true,
            image_class_list: [
              {title: 'Width100', value: 'image100'},
            ], 
            mobile: {
                height:300
            },
            setup: function (editor) {
                editor.on('init', function (e) {
                  editor.setContent(`${existingNotes}`);
                });
            }
            
        });

        $('#ViewHighlightModal').modal('toggle')
    });


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
    
    url = '/app/archivehighlight/'+id
    $.get(url)
    .done(function(){
        alert = create_alert('alert-danger',`
        <ul>
        <li>
            Highlight has been deleted. <button type="button" data-dismiss="alert" onclick="UnarchiveHighlight(${id})"class="main-button ">UNDO</button>
        </li>
        </ul>
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      `)
        byId('flashMessages').appendChild(alert)
    });

    }
    else{
        highlights = Array.from(byClass(`highlight${id}`))
        //console.log(highlights)
        highlights.forEach(clearHighlight)
        url = `https://${window.location.host}/app/archivehighlight/${id}`
        $.get(url)

        var updated_content = byId('article_content').innerHTML
        $.post('/app/article/' + article_uuid + '/highlight-storage', {
          'updated_content': updated_content
        });




    }
    
    
    
}

function UnarchiveHighlight(id){
    byId(`highlight-${id}`).style.display = 'none'
    console.log('highlight hidden')
    
    url = '/app/unarchivehighlight/'+id
    $.get(url)
    .done(function(){
        byId(`highlight-${id}`).style.display = 'block'

        alert=create_alert('alert-success',`
        <ul>
        <li>
            Highlight has been unarchived.
        </li>
        </ul>
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      `)
      byId('flashMessages').appendChild(alert)
    });
    
}




    
function UpdateHighlight(id, review=false){
    $('#ViewHighlightModal').modal('hide')
    
    var doc_tags,tags,untags, doc_topics, activetopics, untopics, notes, highlight, topicspace
    

    // notes = byId('view_highlight_notes').value
    // highlight = byId('view_highlight_text').value
   

    notes = tinymce.get('view_highlight_notes').getContent()
    highlight = tinymce.get('view_highlight_text').getContent()
    console.log(highlight)
    untopics = nonmember_list
    activetopics = []
    Array.from(byClass('member')).forEach(t => activetopics.push(t.innerText));
    console.log(activetopics)

    
    
    data = {
        'notes': notes,
        'highlight':highlight,
        'topics':activetopics,
        'untopics':untopics,
        // 'tags':tags,
        // 'untags':untags,
        // 'atags':false,
        //'atopics':false,
        'topics-page':'false',
        'do_not_review': byId('do_not_review').checked
    }
    
    
    data = JSON.stringify(data)
    console.log(data)
       
    url = '/app/view_highlight/' + id
    
    $.post(url, {
        'data':data
    }).done(function( data ) {
        data = JSON.parse(data)
        topics = data['topics']
        console.log(topics)
        // if (typeof apply_filters === "function") { 
        //     console.log('apply filters exists')
        //     apply_filters()
        // }
        
    }); 

}

