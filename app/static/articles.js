
const byId = function(id){
    return document.getElementById(id);
};

const byClass = function(classname){
return document.getElementsByClassName(classname);
};

document.addEventListener("DOMContentLoaded", initialize());



function ViewArticle(id){

    $.get('/view_article/' + id, function(data) {
        var modal = byId('edit_article');
        console.log(modal);
        modal.innerHTML = data;
        initialize();
        $('#edit_article').modal('toggle');
    });
}



    
function edit_article(){

    var not_editing = byClass('not-editing');
    var editing = byClass('editing');

    for (var i=editing.length-1; i >= 0; i--){
        
        if (not_editing[i]){
            not_editing[i].style.display = "none";
        }

        editing[i].classList.remove('editing');
    
        
    }

}

var add;

function initialize(){

    

    var tagged =  byClass('tagged');
    var untagged = byClass('untagged');
    add = byId('add_new_tag');

    for (var i = 0; i<tagged.length; i++){
        tagged[i].addEventListener("click", function(e) {
            e=e || window.event;
            var target = e.target || e.srcElement;

            
            if (target.tagName === 'LABEL'){
                console.log("target = label")

                if (target.classList.contains('tagged')){
                    target.classList.remove('tagged');
                    target.classList.add('untagged')
                }
                else{
                    target.classList.remove('untagged');
                    target.classList.add('tagged')
                }
            }
                
        
        });
    }

    for (var i = 0; i<untagged.length; i++){

        untagged[i].addEventListener("click", function(e) {
            e=e || window.event;
            var target = e.target || e.srcElement;

            
            if (target.tagName === 'LABEL'){
                console.log("target = label")

                if (target.classList.contains('tagged')){
                    target.classList.remove('tagged');
                    target.classList.add('untagged')
                }
                else{
                    target.classList.remove('untagged');
                    target.classList.add('tagged')
                }
            }
        
        
        });
    }
    
    


}




function add_tag_start(){
    add.innerHTML = `
    <form>
        <button type="submit" disabled style="display: none" aria-hidden="true"></button>
        <div class="form-row align-items-center">
            <div class="col-auto">
                <label class="sr-only" for="inlineFormInput">Name</label>
                <input id = "add_tag_input" type="text" class="form-control mb-2" id="inlineFormInput" placeholder="Tag">
                <input disabled style="display: none" aria-hidden="true"></input>

            </div>
            <div class="col-auto">
                <button id = "submit_new_tag" type="button" onclick = "add_tag_finish()" class="btn mb-2">Add</button>
                <button type="button" class="btn cancel mb-2" onclick="add_tag_cancel()">Cancel</button>
            </div>
        </div>
    </form>
    `;
    var input = document.getElementById('add_tag_input');
    input.focus();
    // Execute a function when the user releases a key on the keyboard
    input.addEventListener("keyup", function(event) {
        // Number 13 is the "Enter" key on the keyboard
        if (event.keyCode === 13) {
            // Cancel the default action, if needed
            event.preventDefault();
            // Trigger the button element with a click
            document.getElementById("submit_new_tag").click();
        }
    }); 


}

function add_tag_cancel(){
    add.innerHTML = `
    <button id="add_new_button" onclick = "add_tag_start()" class = "btn add_new">Add New</button>
    `;
}



function add_tag_finish(){
    var new_tag = document.getElementById('add_tag_input').value;

    add.innerHTML = `
    <button id="add_new_button" onclick = "add_tag_start()" class = "btn add_new">Add New</button>
    `;

    var new_label = document.createElement('label');
    new_label.innerHTML = new_tag;
    new_label.classList.add('tagged');


    var new_input = document.createElement('input');
    new_input.name = "tags";
    new_input.value = new_tag;
    new_input.type = "checkbox";
    new_input.checked = true;

    new_label.appendChild(new_input);

    new_label.addEventListener("click", function(e) {
        e=e || window.event;
        var target = e.target || e.srcElement;

        
            if (target.tagName === 'LABEL'){
                console.log("target = label")

                if (target.classList.contains('tagged')){
                    target.classList.remove('tagged');
                    target.classList.add('untagged')
                }
                else{
                    target.classList.remove('untagged');
                    target.classList.add('tagged')
                }
            }
            
    });

    

    document.getElementById('new_tags').appendChild(new_label);

    
}
function article_updated(article_id, data){
    var a = byId(`article${article_id}`);
    a.innerHTML = data;
}


function save(article_id){

    var doc_tags,doc_remove_tags, tags, title, read_status, notes, content, data;

    console.log('saving');

    doc_tags = byClass('tagged');
    doc_remove_tags = byClass('untagged');
    tags = [];
    remove_tags = [];

    for (var i = 0; i < doc_tags.length; i++){
        tags.push(doc_tags[i].firstElementChild.value); 
    };

    for (var i = 0; i < doc_remove_tags.length; i++){
        remove_tags.push(doc_remove_tags[i].firstElementChild.value); 
    };
    

    title = byId('title_edit').value;
    read_status = byId('read_edit').value;
    notes = byId('notes_edit').value;
    content = byId('content_edit').value;

    data = {
        'title': title,
        'read_status': read_status,
        'notes': notes,
        'content': content,
        'tags':tags,
        'remove_tags': remove_tags
    }


    $.post('/articles/' + article_id + '/update', {
            'data':JSON.stringify(data)
        }).done(function( data ) {
            article_updated(article_id, data)
        }); 

}



