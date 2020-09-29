var input, destination, topicspace 

initialize();

function AddTopicReset(){
   destination.innerHTML= `<button class="main-button cancel" onclick="AddTopicStart()">Add new</button>`
}

function AddTopicStart(){
    destination = byId('add-topic-destination')

    destination.innerHTML = `
        <input class = "lurnby-text-input" type="text" id="AddTopicInput" placeholder="Topic title ..."></input> 
        <button type="button" onclick="AddTopicSubmit()" class="main-button add">add</button>
        <button type="button" class="main-button edit" onclick="AddTopicReset()">cancel</button>  
    `
    
    input = byId('AddTopicInput')
    input.focus()
}



function AddTopicSubmit(){
    input = byId('AddTopicInput')

    
    if (input.value == '' || input.value == ' ' || input.value == '  ')
    {
        input.classList.add('is-invalid')
        input.focus();
    }
    else
    {
        topicspace = byId('topics_all')
        topicspace.innerHTML=`
        <div class = "loading">
            <p>Loading...</p>
            <svg xmlns="http://www.w3.org/2000/svg" style="margin:auto;background:0 0" width="64" height="64" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid" display="block"><circle cx="50" cy="50" fill="none" stroke="#e3e3e3" stroke-width="5" r="32" stroke-dasharray="150.79644737231007 52.26548245743669" transform="rotate(144.01 50 50)"><animateTransform attributeName="transform" type="rotate" repeatCount="indefinite" dur="1s" values="0 50 50;360 50 50" keyTimes="0;1"/></circle></svg>
        </div>
        `

        $.post('/topics/add', {
            title: input.value
        }).done(function(response) {
            //destination.innerHTML= `<button class="main-button cancel" onclick="AddTopicStart()">Add new</button>`
            topicspace.innerHTML = response;
            initialize();
        }).fail(function(xhr) {
            
            topicspace.innerHTML = xhr.responseText
            destination = byId('add-topic-destination')            
            destination.innerHTML ='<div class="alert alert-danger alert-dismissible fade show" role="alert">There is already a topic with that title.<button onclick = "AddTopicReset()" type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button></div>'
            initialize();
        });
        
    
    }
}

function filter(){

    

    var tagged = byClass('tagged')
    filter_tags = []
    filter_topics = []

  

    for (var i =0; i < tagged.length; i++){

        if (tagged[i].classList.contains('filter-tag')){
            filter_tags.push(tagged[i].firstElementChild.value);
        }
        else if (tagged[i].classList.contains('filter-topic')){
            filter_topics.push(tagged[i].firstElementChild.value);
        }
    }

    topicspace = byId('topics_all')
    topicspace.innerHTML=`
    <div class = "loading">
        <p>Loading...</p>
        <svg xmlns="http://www.w3.org/2000/svg" style="margin:auto;background:0 0" width="64" height="64" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid" display="block"><circle cx="50" cy="50" fill="none" stroke="#e3e3e3" stroke-width="5" r="32" stroke-dasharray="150.79644737231007 52.26548245743669" transform="rotate(144.01 50 50)"><animateTransform attributeName="transform" type="rotate" repeatCount="indefinite" dur="1s" values="0 50 50;360 50 50" keyTimes="0;1"/></circle></svg>
    </div>
    `

    data = {
        'topics': filter_topics,
        'tags': filter_tags
    }

    data = JSON.stringify(data)
    console.log(data)

    $.post('/topics/filter', {
       data:data
    }).done(function(response) {
        //destination.innerHTML= `<button class="main-button cancel" onclick="AddTopicStart()">Add new</button>`
        topicspace.innerHTML = response;
        initialize();
    }).fail(function(xhr) {
        topicspace.innerHTML = xhr.responseText;
        destination = byId('add-topic-destination');        
        destination.innerHTML ='<div class="alert alert-danger alert-dismissible fade show" role="alert">Something went wrong, please try again.<button onclick = "AddTopicReset()" type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button></div>'
        initialize();
    });


}