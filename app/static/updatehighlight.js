
function RemoveFromTopic(id, title){
    newId = '"' + id + '"'
    newTitle = '"' + title + '"'
    
    var nonmembers = document.getElementById('NonMembers')
    var removeMember = document.getElementById(id)
    
    var newLabel = document.createElement('label')
    newLabel.setAttribute('id', id)
    newLabel.classList.add('topic-non-member', 'btn', 'btn-default')
    newLabel.setAttribute('onclick', 'AddToTopic(' + newId + ',' + newTitle + ')')
    
    var newSpan = document.createElement('span')
    newSpan.innerHTML = '<input name = "nonmembers" type="checkbox" checked value="' + title + '">' + title + '<span class="topic-icon"><i class="fa fa-plus fa-xs" aria-hidden="true"></i></span>'
    
    newLabel.append(newSpan)
    nonmembers.append(newLabel)
    
    removeMember.parentNode.removeChild(removeMember);
}
    
    
function AddToTopic(id, title){
    newId = '"' + id + '"'
    newTitle = '"' + title + '"'

    var members = document.getElementById('Members')
    var removeMember = document.getElementById(id)

    var newLabel = document.createElement('label')
    newLabel.setAttribute('id', id)
    newLabel.classList.add('topic-member', 'btn', 'btn-default')
    newLabel.setAttribute('onclick', 'RemoveFromTopic(' + newId + ',' + newTitle + ')')
    
    var newSpan = document.createElement('span')

    newSpan.innerHTML = '<input name = "members" type="checkbox" checked value="' + title + '">' + title + '<span class="topic-icon"><i class="fa fa-times" aria-hidden="true"></i></span>'

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
                            }
                        );
                
    
    $('#ViewHighlightModal').modal('toggle')

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

function UpdateNewTopic(){
    $('#Update-CreateTopic').html('<div class = "form-row align-items-center"> <div class="col-sm-6 my-1"> <input autofocus="" class="form-control" id="UpdateAddTopicInput" name="title" placeholder="Topic title..." required="" type="text" value=""></input></div> <div class="col-auto my-1"> <button type="button" onclick="UpdateCancelNewTopic()" class="btn btn-outline-secondary">cancel</button> </div>  <div class="col-auto my-1"> <button onclick="UpdateNewTopicSubmit()" type="button" class="btn btn-primary">add</button> </div> </div> ');
    $('#UpdateAddTopicInput').trigger('focus');
  }

  function UpdateCancelNewTopic(){
    $('#Update-CreateTopic').html('<button onclick ="UpdateNewTopic()" class="create-button btn btn-success">Create new topic </button>')
  }


  function UpdateNewTopicSubmit(){
    $.post('/topics/add', {
      title: $('#UpdateAddTopicInput').val()
    }).done(function(response) {
        $('#Update-CreateTopic').html('<button onclick ="UpdateNewTopic()" class="create-button btn btn-success">Create new topic </button>');
        AddToTopic(response['id'], response['title'])
    }).fail(function() {
        $('#Update-CreateTopic').html('<div class="alert alert-danger alert-dismissible fade show" role="alert">There is already a topic with that title.<button onclick = "UpdateNewTopic()" type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button></div>')
    });
}

