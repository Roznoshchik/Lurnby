
const byId = function(id){
    return document.getElementById(id);
};

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





function add_tag_start(){
   

    add.innerHTML = `
        <button type="submit" disabled style="display: none" aria-hidden="true"></button>
        <div class="form-row align-items-center">
            <div class="col-auto">
                <label class="sr-only" for="inlineFormInput">Name</label>
                <input id = "add_tag_input" type="text" class="form-control mb-2" id="inlineFormInput" placeholder="Tag" required>
                <input disabled style="display: none" aria-hidden="true"></input>

            </div>
            <div class="col-auto">
                <button id = "submit_new_tag" type="button" onclick = "add_tag_finish()" class="main-button add-new">Add</button>
                <button type="button" class="btn cancel mb-2" onclick="add_tag_cancel()">Cancel</button>
            </div>
        </div>
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
    <button id="add_new_button" onclick = "add_tag_start()" class = "main-button add_new">Add New</button>
    `;
}



function add_tag_finish(){
    var new_tag = document.getElementById('add_tag_input').value;

    if (new_tag == ''){
        byId('add_tag_input').classList.add('is-invalid')
        return;
    }

    add.innerHTML = `
    <button id="add_new_button" onclick = "add_tag_start()" class = "main-button add_new">Add New</button>
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




function RemoveFromTopic(id, title){
    newId = '"' + id + '"'
    newTitle = '"' + title + '"'
    
    var nonmembers = document.getElementById('NonMembers')
    var removeMember = document.getElementById(id)
    
    var newLabel = document.createElement('label')
    newLabel.setAttribute('id', id)
    newLabel.classList.add('topic-label', 'btn')
    newLabel.setAttribute('onclick', 'AddToTopic(' + newId + ',' + newTitle + ')')
    
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

                            }
                        );
                
    
    $('#ViewHighlightModal').modal('toggle')
    
    const byId = function(id){
        return document.getElementById(id);
    };
    
    

}
    
    
    
function UpdateHighlight(id){

    $('#ViewHighlightModal').modal('hide')

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
    

}

