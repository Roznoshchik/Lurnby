
document.addEventListener("DOMContentLoaded", initialize());


$('#edit_article').on('hidden.bs.modal', function (e) {
    
    byId('edit_article').innerHTML = '';
})

$('#add_article').on('hidden.bs.modal', function (e) {
    byId('add_article').innerHTML = '';
})

function clear_modals(){

    $('#add_article').modal('hide')    
    $('#edit_article').modal('hide') 
    byId('edit_article').innerHTML='';
    byId('add_article').innerHTML='';
}



/* add article form functions */




function add_web(){
    byId('add_from').innerHTML = `
    <div class = "article_data_group">
        <p class = "small">Add articles easily with our <a href="https://chrome.google.com/webstore/detail/lurnby/dpobgbljepcemmnbfflkcplalobfllgn" target="_blank">Chrome</a> or <a href = "https://addons.mozilla.org/en-US/firefox/addon/lurnby/" target="_blank">Firefox</a> extensions.</p>     
        <h6>Article URL</h6>
        <input style = "width:100%;" type = "text" id = "url_add" placeholder="http://..." required></input>
    </div>
    `
    byId('url_add').focus()
}


function add_epub(){
    byId('add_from').innerHTML = `
    <div class = "article_data_group">
        <h6>Add epub</h6>
        <input class = "epub-input" id="epub_add" type="file"></input>
        <label class="main-button add_new epub-label" for="epub_add">choose a file</label>
        </div>
    `

    var input = byId('epub_add');
    console.log('got input')
    console.log(input)
    var label = input.nextElementSibling, labelVal=label.innerHTML;

    input.addEventListener('change', function(e){
        console.log('added event listener?');
        console.log(input.value)
        var fileName = '';
        if (this.files){
            fileName = e.target.value.split( '\\' ).pop();            
        };

        if (fileName){
            label.innerHTML=fileName;
        }
        else {
            label.innerHTML = labelVal;
        }
    });

}

function add_manual(){
    byId('add_from').innerHTML = `
    <div class = "article_data_group manual_add">
        <h6>Title</h6>
        <input style = "width:100%;" type = "text" id = "title_add" required placeholder="Article title ..."></input>
        <h6>Source</h6>
        <input style = "width:100%;" type = "text" id = "source_add" placeholder="Where the article is from ..."></input>
        <h6>Text</h6>
        <textarea id = "content_add" placeholder="Paste article text here ..."></textarea>
    </div>
    `

    byId('title_add').focus()
}

function add_new_article(){

    var title='none', source='none', tags=[], notes='none',content='none', url='none', epub='none', doc_tags; 
    doc_tags=byClass('article-tag');
    Array.prototype.forEach.call(doc_tags, function(tag){
        if (tag.classList.contains('tagged')){
            tags.push(tag.firstElementChild.value);
        };
    });
   
    byId('articles_page').innerHTML = `<div style = "display: block; text-align:center; float:center; margin:auto; margin-top: 88px; padding:88px; background: white; border:black 2px solid; width: 500px;">
    <p>Articles with a lot of images take some time to process. Please wait.</p>
    <img src="static/spinning-circles.svg" width="50" alt="">
</div>`;

    formdata = new FormData();

    notes = byId('notes_add').value;

 
    if (byId('title_add')){
        title = byId('title_add').value;
    };
    if (byId('source_add')){
        source = byId('source_add').value ; 

    };
    
    if (byId('url_add')){
        url = byId('url_add').value;

    };


    if (byId('epub_add')){
        epub = 'true'
        epub_file = byId('epub_add').files[0];
        formdata.append('epub_file', epub_file);
    }
    formdata.append('epub', epub);



    if (byId('content_add')){
        content = byId('content_add').value;
    };
    


    formdata.append('notes', notes);
    formdata.append('tags', JSON.stringify(tags));
    formdata.append('title', title);
    formdata.append('source', source);
    formdata.append('url', url);
    formdata.append('content', content);

    
    $.ajax({
        url:'/articles/new',
        data:formdata,
        type:'POST',
        contentType: false,
        processData: false,
    }).done(function(response){
        byId('articles_page').innerHTML = response;
        
        var alert = document.createElement('div')
        alert.classList.add('main-alert','fade','show', 'alert','alert-dismissable', 'alert-success')
        alert.setAttribute('role', 'alert')
        alert.innerHTML = `Article added! <button type="button" class="close" data-dismiss="alert" aria-label="Close">
        <span aria-hidden="true">&times;</span>
        </button>
     `
        
       

        var flash = byId('flashMessages')
        flash.appendChild(alert);


        
    }).fail(function(xhr) {
      
        response = JSON.parse(xhr.responseText)
        if (response['not_epub']){
            var alert = document.createElement('div')
            alert.classList.add('main-alert', 'alert','fade','show','alert-dismissable', 'alert-danger')
            alert.setAttribute('role', 'alert')
            alert.innerHTML = `Only .epub files are accepted.<button type="button" class="close" data-dismiss="alert" aria-label="Close">
                                <span aria-hidden="true">&times;</span>
                                </button>`

            var flash = byId('flashMessages')
            flash.appendChild(alert);        
        }
        if (response['bad_url']){
            var alert = document.createElement('div')
            alert.classList.add('main-alert', 'alert','fade','show','alert-dismissable', 'alert-danger')
            alert.setAttribute('role', 'alert')
            alert.innerHTML = `Please check the url and try again.<button type="button" class="close" data-dismiss="alert" aria-label="Close">
                                <span aria-hidden="true">&times;</span>
                                </button>`

            var flash = byId('flashMessages')
            flash.appendChild(alert);
        }
        if (response['manual_fail']){
            var alert = document.createElement('div')
            alert.classList.add('main-alert', 'alert','fade','show','alert-dismissable', 'alert-danger')
            alert.setAttribute('role', 'alert')
            alert.innerHTML = `Something went wrong, please try again. <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                                <span aria-hidden="true">&times;</span>
                                </button>`

            var flash = byId('flashMessages')
            flash.appendChild(alert);
        }
        if (response['no_article']){
            var alert = document.createElement('div')
            alert.classList.add('main-alert', 'alert','alert-dismissable', 'alert-danger')
            alert.setAttribute('role', 'alert')
            alert.innerHTML = `Something went wrong, please try again.  <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                                <span aria-hidden="true">&times;</span>
                                </button>`

            var flash = byId('flashMessages')
            flash.appendChild(alert);
        }

        
    });


/*
    $.post('/articles/new', {
        'epub': epub,
        'url':url,
        'notes':notes,
        'tags': JSON.stringify(tags),
        'title': title,
        'source':source,
        'content':content
        }).done(function( data ) {
        console.log(data)
    }); 
*/
}



/*  end add article form  */

function view_article_tiny_init(){
    console.log('pulling up an article')

    var existing_notes = byId('notes_edit').value

    // cancels any existing editing tiny editors?
    console.log('made it here')
    if (byId('content_edit') != null){
        var existing_content = byId('content_edit').value
        tinymce.EditorManager.execCommand('mceRemoveEditor',true, 'content_edit');
    }

    tinymce.EditorManager.execCommand('mceRemoveEditor',true, 'notes_edit');
    tinymce.EditorManager.execCommand('mceRemoveEditor',true, 'article_content');
    tinymce.EditorManager.execCommand('mceRemoveEditor',true, 'article_notes');



  //notes preview
  tinymce.init({
    selector: '#article_notes',
    menubar: false,
    resize: 'vertical',
    toolbar: false,
    skin: "oxide",
    content_css: "light",
    mobile: {
        height: 300
    },
  	readonly: 1,
    
    setup: function (editor) {
    editor.on('init', function (e) {
      editor.setContent(`${existing_notes}`);
      });
    }

  });
  
  console.log('notes_initialized')
    
  if(byId('article_content') != null){
    //content preview
  tinymce.init({
    selector: '#article_content',
    menubar: false,
    resize: 'vertical',
    toolbar: false,
    skin: "oxide",
    content_css: "light",
    mobile: {
        height: 300
    },
    readonly: 1,

    setup: function (editor) {
    editor.on('init', function (e) {
      editor.setContent(`${existing_content}`);
      });
    }

  });
  console.log('content initialized')
  }
  
}

function edit_article_tiny_init(){
  
  //preview remove
  tinymce.EditorManager.execCommand('mceRemoveEditor',true, 'article_content');
  
  if (byId('article_content') != null){
    byId('article_content').style.display = "none"
  }
   
  tinymce.EditorManager.execCommand('mceRemoveEditor',true, 'article_notes');
   byId('article_notes').style.display = "none"


 
  
  //notes edit
  tinymce.EditorManager.init({
          selector: '#notes_edit',
          menubar: 'insert format',
          resize: 'vertical',
          toolbar: 'styleselect | bold italic underline | hr',
          skin: "oxide",
          content_css: "light",  
          plugins: 'link hr', 
          mobile: {
              height:300
          }

    });
    console.log('notes edit initialized')        
  if (byId('content_edit') != null){
        //content edit
        tinymce.EditorManager.init({
            selector: '#content_edit',
            menubar: 'insert format',
            resize: 'vertical',
            toolbar: 'styleselect | bold italic underline | hr',
            skin: "oxide",
            content_css: "light",  
            plugins: 'link hr', 
            mobile: {
                height: 300
            }
            
        });
        console.log('content edit initialized')

    }
   
}


function ViewArticle(id){

    $.get('/view_article/' + id, function(data) {
        var modal = byId('edit_article');
        modal.innerHTML = data;
        initialize();
        //intialize tiny mce here?
        view_article_tiny_init()
        $('#edit_article').modal('toggle');
    });
}

function ViewAddArticle(){

    $.get('/view_add_article/', function(data) {
        var modal = byId('add_article');
        modal.innerHTML = data;
        initialize();
        // initialize tinymce here?

        $('#add_article').modal('toggle');
    });
}


    
function edit_article(){

    edit_article_tiny_init()

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



function add_tag_start(string){
    var target
    if (string == 'article-tag'){
        target = 'article-tag'
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
    new_label.innerHTML = new_tag;
    new_label.classList.add('tagged', string);


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
/*
function article_updated(article_id, data){
    var a = byId(`article${article_id}`);
    a.innerHTML = data;
}
*/

function article_updated(data){
    var a = byId('articles_page');
    a.innerHTML = data;
    initialize();
}

function filter(){
    console.log('filter()')
    var doc_tags = byClass('tagged');
    console.log(doc_tags)
    var tags = []
    
    for (var i = 0; i <doc_tags.length; i++){
        tags.push(doc_tags[i].firstElementChild.value);
    }
    
    data = {
        'tags':tags,
    }


    $.post('/articles/filter', {
            'data':JSON.stringify(data)
        }).done(function( data ) {
            article_updated(data)
        }); 
}


function save(article_id){

    var doc_tags,doc_remove_tags, tags, title, read_status, notes, content, data;

    console.log('saving');

    doc_tags = byClass('tagged');
    doc_remove_tags = byClass('untagged');
    tags = [];
    remove_tags = [];
    if (doc_tags){
        for (var i = 0; i < doc_tags.length; i++){
            if (doc_tags[i].classList.contains('filter-tag') || doc_tags[i].classList.contains('new-article-tag')){
                continue;
            }
    
            tags.push(doc_tags[i].firstElementChild.value); 
        };
    }
  
    if (doc_remove_tags){
        for (var i = 0; i < doc_remove_tags.length; i++){
            if (doc_remove_tags[i].classList.contains('filter-tag') || doc_remove_tags[i].classList.contains('new-article-tag')){
                continue;
            }
            remove_tags.push(doc_remove_tags[i].firstElementChild.value); 
        };
    }
    
    

    title = byId('title_edit').value;
    read_status = byId('read_edit').value;
    
    notes = tinymce.get('notes_edit').getContent()
    console.log(notes)
    content = tinymce.get('content_edit').getContent()
    
    //notes = byId('notes_edit').value;
    //content = byId('content_edit').value;

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
            article_updated(data)
        }); 

}



