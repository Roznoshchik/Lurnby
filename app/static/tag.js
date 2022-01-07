var add;


function initialize(){
    console.log('initializing')
    var tagged =  byClass('tagged');
    var untagged = byClass('untagged');
    add = byId('add_new_tag');

    for (var i = 0; i<tagged.length; i++){
        if (tagged[i].classList.contains('initialized')){
            continue;
        }
        else {
            tagged[i].classList.add('initialized');
            tagged[i].addEventListener("click", function(e) {
                e=e || window.event;
                var target = e.target || e.srcElement;
    
                
                if (target.tagName === 'LABEL'){
                    target.classList.toggle('tagged')
                    target.classList.toggle('untagged')

                    //console.log("target = label")
                    /*
                    if (target.classList.contains('tagged')){
                        target.classList.remove('tagged');
                        target.classList.add('untagged')
                        target.firstChild.name = 'untags';
                        target.firstChild.checked=true;
    
    
    
                    }
                    else{
                        target.classList.remove('untagged');
                        target.classList.add('tagged')
                        target.firstChild.name = 'tags';
                        target.firstChild.checked=true;
    
                    }
                    */
                }  
            
            });
            
        }
    }

    for (var i = 0; i<untagged.length; i++){
        if (untagged[i].classList.contains('initialized')){
            continue;
        }
        else {
            untagged[i].classList.add('initialized');
            untagged[i].addEventListener("click", function(e) {
                e=e || window.event;
                var target = e.target || e.srcElement;
                if (target.tagName === 'LABEL'){
                    target.classList.toggle('tagged')
                    target.classList.toggle('untagged')
                }
            });
        }
    }
}



function add_tag_start(string){
    var target
    if (string == 'article-tag'){
        target = 'article-tag'
    }
    else if(string='update-highlight'){
        target = 'update-highlight'
    }
    else {
        target = 'view-article-tag'
    }
    
    
    add.innerHTML = `
    <form>
        <button type="submit" disabled style="display: none" aria-hidden="true"></button>
        <div class="form-row align-items-center">
            <div class="col-auto">
                <label class="sr-only" for="inlineFormInput">Name</label>
                <input id = "add_tag_input" type="text" class="form-control mb-2" id="inlineFormInput" placeholder="Tag" required>
                <input disabled style="display: none" aria-hidden="true"></input>

            </div>
            <div class="col-auto">
                <button id = "submit_new_tag" type="button" onclick = "add_tag_finish('${target}')" class="main-button add-new">Add</button>
                <button type="button" class="btn cancel mb-2" onclick="add_tag_cancel('${target}')">Cancel</button>
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

function add_tag_cancel(string){
    

    add.innerHTML = `
    <button id="add_new_button" onclick = "add_tag_start('${string}')" class = "main-button add_new">Add New</button>
    `;
}



function add_tag_finish(string){
    var new_tag = document.getElementById('add_tag_input').value;

    if (new_tag == ''){
        byId('add_tag_input').classList.add('is-invalid')
        return;
    }

    add.innerHTML = `
    <button id="add_new_button" onclick = "add_tag_start('${string}')" class = "main-button add_new">Add New</button>
    `;

    var new_label = document.createElement('label');
    //new_label.innerHTML = new_tag;
    new_label.classList.add('tagged', string, 'initialized');


    var new_input = document.createElement('input');
    new_input.name = "tags";
    new_input.value = new_tag;
    new_input.type = "checkbox";
    new_input.checked = true;

    var new_span=document.createElement('span');
    new_span.innerText=new_tag

    new_label.appendChild(new_input);
    new_label.appendChild(new_span)

    new_label.addEventListener("click", function(e) {
        e=e || window.event;
        var target = e.target || e.srcElement;

        
            if (target.classList.contains('tagged')){
                    target.classList.remove('tagged');
                    target.classList.add('untagged')
                    
                    target.firstChild.name = 'untags';
                    target.firstChild.checked=true;
             


                }
                else{
                    target.classList.remove('untagged');
                    target.classList.add('tagged')
                    target.firstChild.name = 'tags';
                    target.firstChild.checked=true;

                }
            
    });

    document.getElementById('new_tags').appendChild(new_label);
    
}

//////////////////////////////////////////
//                                      //
//          Tag page functions          //
//                                      //
//////////////////////////////////////////

const editTag = (type, id) => {    
    byId(type+'-'+id).innerHTML = createEditTag(type == 'tag' ?tags[`${id}`]:topics[`${id}`])
}

const createTag = (tag) => {
    return ` 
    <div class="header">
        <h6>${tag.name}</h6>
        <div class="underline"></div>
    </div>
    <div class="content">
        <p>${tag.type == 'topic'? 'Highlights':'Articles'}: ${tag.records}</p>

        <div id ="${tag.type}-${tag.id}-actions" class="actions">
            <button onclick = "editTag('${tag.type}',${tag.id})" class="main-button ml0 ">Edit</button>
        </div>
    </div>`

}

const createEditTag = (tag) => {    
    return ` 
    <div class="header">
        <div class="form-label-group">
            <input  class="form-control" id="${tag.type}-${tag.id}-name" name=tag-name type="text" value="${tag.name}"/>
            <label for="tag-name">Title</label>
        </div>
        <div class="underline"></div>
    </div>
    <div class="content">
        <p>${tag.type == 'topic'? 'Highlights':'Articles'}: ${tag.records}</p>

        <div id ="${tag.type}-${tag.id}-actions" class=" flex actions">
            <button onclick = "archiveTag('${tag.type}',${tag.id})" class="main-button ml0 ">Archive</button>
            <button onclick = "updateTag('${tag.type}',${tag.id})" class="main-button mlauto ">Save</button>
        </div>
    </div>`
}

const updateTag = (type, id) => {
    const newName = byId(`${type}-${id}-name`).value;
    type == 'tag' ? tags[`${id}`].name = newName : topics[`${id}`].name = newName;
    byId(`${type}-${id}`).innerHTML = createTag(type == 'tag' ? tags[`${id}`]:topics[`${id}`])
    const tag = type == 'tag' ? tags[`${id}`] : topics[`${id}`]
    const url = '/app/tags'
    fetchTag(url, tag)
}

const archiveTag = (type, id) => {
    byId(`${type}-${id}`).remove()
    const tag = type == 'tag' ? tags[`${id}`] : topics[`${id}`]
    tag.archived = true
    const url = '/app/tags/archive'
    fetchTag(url, tag)
}

const fetchTag = (url, data) => {
    return fetch(url,{ 
        method:'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrf_token
        },
        body: JSON.stringify(data) 
    })
    .catch(error => {
        setTimeout(fetchTag.bind(null,url, data), 10000)
    });
} 