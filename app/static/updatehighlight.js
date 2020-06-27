
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
    $('#Update-CreateTopic').html('<br> <div class = "form-row align-items-center"> <div class="col-sm-6 my-1"> {{ addtopicform.title(class="form-control", id ="addtopicinput", placeholder="Topic title...", required=true, autofocus=true)}} </div> <div class="col-auto my-1"> <button type="button" onclick="CancelNewTopic()" class="btn btn-outline-secondary">cancel</button> </div>  <div class="col-auto my-1"> <button onclick="NewTopicSubmit()" type="submit" class="btn btn-primary">add</button> </div> </div> </form>');
    $('#addtopicinput').trigger('focus');
  }