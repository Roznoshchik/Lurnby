
document.addEventListener("DOMContentLoaded", initialize());


$('#edit_article').on('hidden.bs.modal', function (e) {

    byId('edit_article').innerHTML = '';
})

$('#add_article').on('hidden.bs.modal', function (e) {
    byId('add_article').innerHTML = '';
})

function clear_modals() {

    $('#add_article').modal('hide')
    $('#edit_article').modal('hide')
    byId('edit_article').innerHTML = `<div class="modal-dialog modal-lg">
    <div class="modal-content">
        <div class="modal-header">
            <button type="button"  class="close" data-dismiss="modal" onclick="clear_modals()" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        </div>
        <div class="modal-body">
            <div class ='rendering'>
                <p>Pulling up the article. Please wait.</p>
                <img id="rrface" class="star mb-4" src="../static/rrbetterface2.png" alt="" height="100">
            </div>        
        </div>
        <div class="modal-footer">                
          <button type="button" class="main-button not-editing" onclick="clear_modals()" data-dismiss="modal">Close</button>
        </div>
    </div>
</div>`;
    byId('add_article').innerHTML = '';
}



/* add article form functions */


function add_web() {
    byId('add_from').innerHTML = `
    <div class = "article_data_group">
        <p class = "small">Add articles easily with our <a href="https://chrome.google.com/webstore/detail/lurnby/dpobgbljepcemmnbfflkcplalobfllgn" target="_blank">Chrome</a> or <a href = "https://addons.mozilla.org/en-US/firefox/addon/lurnby/" target="_blank">Firefox</a> extensions.</p>     
        <h6>Article URL</h6>
        <input style = "width:100%;" type = "text" id = "url_add" placeholder="http://..." required></input>
    </div>
    `
    byId('url_add').focus()
}


function add_epub() {
    byId('add_from').innerHTML = `
    <div class = "article_data_group">
        <h6>Add epub</h6>
        <input class = "file-input" id="epub_add" type="file"></input>
        <label class="main-button add_new file-label" for="epub_add">choose a file</label>
        </div>
    `

    var input = byId('epub_add');
    //console.log('got input')
    //console.log(input)
    var label = input.nextElementSibling, labelVal = label.innerHTML;

    input.addEventListener('change', function (e) {
        //console.log('added event listener?');
        //console.log(input.value)
        var fileName = '';
        if (this.files) {
            fileName = e.target.value.split('\\').pop();
        };

        if (fileName) {
            label.innerHTML = fileName;
        }
        else {
            label.innerHTML = labelVal;
        }
    });

}

function add_pdf() {
    byId('add_from').innerHTML = `
    <div class = "article_data_group">
        <h6>Add pdf</h6>
        <p>Please note pdf support is experimental and not all pdf's can be parsed properly. Currently, tables and diagrams are not processed correctly and only pdfs composed of text and images have a fighting chance.</p>
        <input class = "file-input" id="pdf_add" type="file"></input>
        <label class="main-button add_new file-label" for="pdf_add">choose a file</label>
        </div>
    `

    var input = byId('pdf_add');
    //console.log('got input')
    //console.log(input)
    var label = input.nextElementSibling, labelVal = label.innerHTML;

    input.addEventListener('change', function (e) {
        //console.log('added event listener?');
        //console.log(input.value)
        var fileName = '';
        if (this.files) {
            fileName = e.target.value.split('\\').pop();
        };

        if (fileName) {
            label.innerHTML = fileName;
        }
        else {
            label.innerHTML = labelVal;
        }
    });

}


function add_manual() {
    //console.log(darkModeOn())
    tinymce.EditorManager.execCommand('mceRemoveEditor', true, 'content_add');
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
    addArticleTinyInit();
    //byId('title_add').focus()
}



function add_new_article() {

    var title = 'none', source = 'none', tags = [], notes = '', content = 'none', url = 'none', epub = 'none', pdf = 'none', doc_tags;
    doc_tags = byClass('article-tag');
    Array.prototype.forEach.call(doc_tags, function (tag) {
        if (tag.classList.contains('tagged')) {
            tags.push(tag.firstElementChild.value);
        };
    });

    byId('articles_page').innerHTML = `<div class ='rendering'>
    <p>Articles with a lot of images take some time to process. Please wait.</p>
    <img id="rrface" class="star mb-4" src="../static/rrbetterface2.png" alt="" height="100">
    </div>`;

    data = {}

    notes = byId('notes_add').value;


    if (byId('title_add')) {
        title = byId('title_add').value;
    };
    if (byId('source_add')) {
        source = byId('source_add').value;

    };

    if (byId('url_add')) {
        url = byId('url_add').value;

    };


    if (byId('epub_add')) {
        epub = 'true'
        file = byId('epub_add').files[0];
        var filename = file.name;
        ext = filename.split('.').pop();
        if (ext != 'epub') {
            data['not_epub'] = true
        }
    }

    data['epub'] = epub

    if (byId('pdf_add')) {
        pdf = 'true'
        file = byId('pdf_add').files[0];
        var filename = file.name;
        ext = filename.split('.').pop();
        if (ext != 'pdf') {
            data['not_pdf'] = true
        }
    }
    data['pdf'] = pdf

    if (byId('content_add')) {
        content = byId('content_add').value;
    };

    data['notes'] = tinymce.get('notes_add').getContent()

    // data['notes'] = notes
    data['tags'] = JSON.stringify(tags)
    data['title'] = title
    data['source'] = source
    data['url'] = url
    // data['content'] = content
    data['content'] = tinymce.get('content_add').getContent()


    /////////////////////////
    //  failure responses  //
    /////////////////////////

    function handleErrors(response) {
        if (!response.ok) {
            response.text().then(function (text) {
                data = JSON.parse(text)
                byId('articles_page').innerHTML = data['html'];


                if (data['not_epub']) {
                    alert = create_alert('alert-danger', `Only .epub files are accepted.<button type="button" class="close" data-dismiss="alert" aria-label="Close">
                                        <span aria-hidden="true">&times;</span>
                                        </button>`)
                }
                if (data['not_pdf']) {
                    alert = create_alert('alert-danger', `That didn't seem to be a pdf file.<button type="button" class="close" data-dismiss="alert" aria-label="Close">
                                        <span aria-hidden="true">&times;</span>
                                        </button>`)
                }
                if (data['bad_url']) {
                    alert = create_alert('alert-danger', `Please check the url and try again.<button type="button" class="close" data-dismiss="alert" aria-label="Close">
                                        <span aria-hidden="true">&times;</span>
                                        </button>`)
                }
                if (data['manual_fail']) {
                    alert = create_alert('alert-danger', `<ul><li>Something went wrong, please try again.</li></ul> <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                                        <span aria-hidden="true">&times;</span>
                                        </button>`)
                }
                if (data['no_article']) {
                    alert = create_alert('alert-danger', `Something went wrong, please try again.  <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                                        <span aria-hidden="true">&times;</span>
                                        </button>`)
                }
                var flash = byId('flashMessages')
                flash.appendChild(alert);
                throw 'Failed to add article'
            })

        }
        return response
    }

    url = '/app/articles/new'
    fetch(url, {
        method: 'post',
        headers: {
            'Content-type': 'application/json',
            'X-CSRFToken': csrf_token
        },
        body: JSON.stringify(data)
    })
        .then(handleErrors)
        .then(response => response.json())
        .then(data => {
            if (!data['processing']) {
                byId('articles_page').innerHTML = data['html'];
                initialize_articles_page()

                alert = create_alert('alert-success', `Article added! <button type="button" class="close" data-dismiss="alert" aria-label="Close">
            <span aria-hidden="true">&times;</span>
            </button>
            `)
                var flash = byId('flashMessages')
                flash.appendChild(alert);

            }
            else {

                az_url = data['url']
                a_id = data['a_id']

                fetch(az_url, {
                    mode: 'cors',
                    method: 'put',
                    body: file
                })
                    .then(function (response) {
                        if (!response.ok) {
                            alert.innerHTML = `Something went wrong, please try again.  <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                                        <span aria-hidden="true">&times;</span>
                                        </button>`

                            var flash = byId('flashMessages')
                            flash.appendChild(alert);
                            throw 'Failed to add article'
                        }
                    })
                    .then(function () {
                        url = `/app/articles/bg`
                        fetch(url, {
                            method: 'post',
                            headers: {
                                'Content-type': 'application/json',
                                'X-CSRFToken': csrf_token
                            },
                            body: JSON.stringify({
                                'a_id': a_id,
                                'tags': JSON.stringify(tags),
                                'pdf': pdf,
                                'epub': epub
                            })
                        })
                            .then(response => response.json())
                            .then(data => article_processing(data['taskID'], a_id))

                    })
            }
        });
}

function article_processing(taskID, a_id) {
    url = `/app/articles/processing/${taskID}/${a_id}`
    fetch(url, {
        method: 'get',
        headers: {
            'Content-type': 'application/html',
            'X-CSRFToken': csrf_token
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data['error']) {
                throw error
            }
            else if (data['processing']) {
                article_processing(taskID, a_id)
            }
            else {
                byId('articles_page').innerHTML = data['html'];

                alert = create_alert('alert-success', `Article added! <button type="button" class="close" data-dismiss="alert" aria-label="Close">
            <span aria-hidden="true">&times;</span>
            </button>
            `)

                var flash = byId('flashMessages')
                flash.appendChild(alert);
            }
        });
}

function addArticleTinyInit() {
    tinymce.EditorManager.init({
        selector: '#content_add',
        menubar: 'insert format',
        resize: 'vertical',
        toolbar: 'styleselect | bold italic underline | numlist bullist | hr | image |code',
        skin: darkModeOn() ? "oxide-dark" : "oxide",
        content_css: darkModeOn() ? "dark" : "light",
        plugins: 'link hr code',
        mobile: {
            height: 300
        }

    });
}

function addArticleNotesInit() {
    tinymce.EditorManager.init({
        selector: '#notes_add',
        menubar: 'insert format',
        resize: 'vertical',
        toolbar: 'styleselect | bold italic underline | numlist bullist | hr | image |code',
        skin: darkModeOn() ? "oxide-dark" : "oxide",
        content_css: darkModeOn() ? "dark" : "light",
        plugins: 'image imagetools lists code link hr',
        // image_dimensions: false,
        object_resizing: true,
        image_class_list: [
            { title: 'Width100', value: 'image100' },
        ],
        mobile: {
            height: 300
        }

    });
}

function view_article_tiny_init() {
    //console.log('pulling up an article')

    var existing_notes = byId('notes_edit').value

    // cancels any existing editing tiny editors?
    if (byId('content_edit') != null) {
        var existing_content = byId('content_edit').value
        tinymce.EditorManager.execCommand('mceRemoveEditor', true, 'content_edit');
    }

    if (byId('reflections_edit')) {
        var existing_reflections = byId('reflections_edit').value
        tinymce.EditorManager.execCommand('mceRemoveEditor', true, 'reflections_edit');
        tinymce.EditorManager.execCommand('mceRemoveEditor', true, 'article_reflections');
    }

    tinymce.EditorManager.execCommand('mceRemoveEditor', true, 'notes_edit');


    tinymce.EditorManager.execCommand('mceRemoveEditor', true, 'article_content');
    tinymce.EditorManager.execCommand('mceRemoveEditor', true, 'article_notes');

    //notes preview
    tinymce.init({
        selector: '#article_notes',
        menubar: false,
        resize: 'vertical',
        toolbar: false,
        skin: darkModeOn() ? "oxide-dark" : "oxide",
        content_css: darkModeOn() ? "dark" : "light",
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
    //console.log('notes_initialized');

    if (byId('article_reflections')) {
        //reflections preview
        tinymce.init({
            selector: '#article_reflections',
            menubar: false,
            resize: 'vertical',
            toolbar: false,
            skin: darkModeOn() ? "oxide-dark" : "oxide",
            content_css: darkModeOn() ? "dark" : "light",
            mobile: {
                height: 300
            },
            readonly: 1,

            setup: function (editor) {
                editor.on('init', function (e) {
                    editor.setContent(`${existing_reflections}`);
                });
            }

        });
        //console.log('reflections_initialized');
    }


    if (byId('article_content') != null) {
        //content preview
        tinymce.init({
            selector: '#article_content',
            menubar: false,
            resize: 'vertical',
            toolbar: false,
            skin: darkModeOn() ? "oxide-dark" : "oxide",
            content_css: darkModeOn() ? "dark" : "light",
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
    }

}

function edit_article_tiny_init() {

    //preview remove
    tinymce.EditorManager.execCommand('mceRemoveEditor', true, 'article_content');

    if (byId('article_content') != null) {
        byId('article_content').style.display = "none"
    }

    tinymce.EditorManager.execCommand('mceRemoveEditor', true, 'article_notes');
    byId('article_notes').style.display = "none"

    tinymce.EditorManager.execCommand('mceRemoveEditor', true, 'article_reflections');
    if (byId('article_reflections')) {
        byId('article_reflections').style.display = "none"
    }




    //notes edit
    tinymce.EditorManager.init({
        selector: '#notes_edit',
        menubar: 'insert format',
        resize: 'vertical',
        toolbar: 'styleselect | bold italic underline | numlist bullist | hr | image |code',
        skin: darkModeOn() ? "oxide-dark" : "oxide",
        content_css: darkModeOn() ? "dark" : "light",
        plugins: 'image imagetools lists code link hr',
        // image_dimensions: false,
        object_resizing: true,
        image_class_list: [
            { title: 'Width100', value: 'image100' },
        ],
        mobile: {
            height: 300
        }

    });
    //console.log('notes edit initialized')  

    if (byId('reflections_edit')) {
        //reflections edit
        tinymce.EditorManager.init({
            selector: '#reflections_edit',
            menubar: 'insert format',
            resize: 'vertical',
            toolbar: 'styleselect | bold italic underline | numlist bullist | hr | image |code',
            skin: darkModeOn() ? "oxide-dark" : "oxide",
            content_css: darkModeOn() ? "dark" : "light",
            plugins: 'image imagetools lists code link hr',
            // image_dimensions: false,
            object_resizing: true,
            image_class_list: [
                { title: 'Width100', value: 'image100' },
            ],
            mobile: {
                height: 300
            }
        });
        //console.log('reflections edit initialized')
    }

    if (byId('content_edit') != null) {
        //content edit
        tinymce.EditorManager.init({
            selector: '#content_edit',
            menubar: 'insert format',
            resize: 'vertical',
            toolbar: 'styleselect | bold italic underline | numlist bullist | hr | image |code',
            skin: darkModeOn() ? "oxide-dark" : "oxide",
            content_css: darkModeOn() ? "dark" : "light",
            plugins: 'image imagetools lists code link hr',
            // image_dimensions: false,
            object_resizing: true,
            image_class_list: [
                { title: 'Width100', value: 'image100' },
            ],
            mobile: {
                height: 300
            }

        });
        //console.log('content edit initialized')
    }

}


function ViewArticle(id) {
    //$('#edit_article').modal('toggle');

    $.get('/app/view_article/' + id, function (data) {
        var modal = byId('edit_article');
        modal.innerHTML = data;
        initialize();
        //intialize tiny mce here?
        view_article_tiny_init()
    });
}

function ViewAddArticle() {

    $.get('/app/view_add_article/', function (data) {
        var modal = byId('add_article');
        modal.innerHTML = data;
        initialize();
        // initialize tinymce here?
        tinymce.EditorManager.execCommand('mceRemoveEditor', true, 'notes_add');
        addArticleNotesInit()
        $('#add_article').modal('toggle');
    });
}

function AddSuggestion() {
    byId('articles_page').innerHTML = `<div class ='rendering'>
    <p>Articles with a lot of images take some time to process. Please wait.</p>
    <img id="rrface" class="star mb-4" src="../static/rrbetterface2.png" alt="" height="100">
    </div>`;

    destination = `/app/articles/add_suggestion`
    fetch(destination, {
        method: 'get',
        headers: {
            'Content-type': 'application/html',
            'X-CSRFToken': '{{ csrf_token() }}'
        }
    })
        .then(response => response.json())
        .then(result => {
            byId('articles_page').innerHTML = result['content'];

            alert = create_alert('alert-success', `Article added! <button type="button" class="close" data-dismiss="alert" aria-label="Close">
        <span aria-hidden="true">&times;</span>
        </button>
     `)
            var flash = byId('flashMessages')
            flash.appendChild(alert);

        });


}




function export_method(id) {
    byId('export').innerHTML = `
    <button type = "button" class = "main-button cancel not-editing" data-dismiss="modal" onclick="export_highlights(${id}, 'json')">Export as JSON</button>
    <button type = "button" class = "main-button cancel not-editing" data-dismiss="modal" onclick="export_highlights(${id}, 'txt')">Export as TXT</button>
    `

}
function export_highlights(id, ext) {
    data = {
        'article_export': true,
        'article_id': id,
        'ext': ext
    }

    $.post('/app/export_highlights', {
        'data': JSON.stringify(data)
    }).done(function (data) {
        data = JSON.parse(data)
        alert = create_alert('alert-success', `
        <ul>
            <li>${data['msg']}</li>
        </ul>
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      `)
        byId('flashMessages').appendChild(alert)
    }).fail(function (data) {
        data = JSON.parse(data)
        alert = create_alert('alert-error', `
          <ul>
              <li>${data['msg']}</li>
          </ul>
          <button type="button" class="close" data-dismiss="alert" aria-label="Close">
            <span aria-hidden="true">&times;</span>
          </button>
       `)
        byId('flashMesssages').appendChild(alert)

    });;
}

function edit_article() {

    edit_article_tiny_init()

    var not_editing = byClass('not-editing');
    var editing = byClass('editing');

    for (var i = editing.length - 1; i >= 0; i--) {

        if (not_editing[i]) {
            not_editing[i].style.display = "none";
        }

        editing[i].classList.remove('editing');


    }

}


var add;

function initialize() {

    var tagged = byClass('tagged');
    var untagged = byClass('untagged');
    add = byId('add_new_tag');

    for (var i = 0; i < tagged.length; i++) {
        tagged[i].addEventListener("click", function (e) {
            e = e || window.event;
            var target = e.target || e.srcElement;


            if (target.tagName === 'LABEL') {
                //console.log("target = label")

                if (target.classList.contains('tagged')) {
                    target.classList.remove('tagged');
                    target.classList.add('untagged')
                }
                else {
                    target.classList.remove('untagged');
                    target.classList.add('tagged')
                }
            }


        });
    }

    for (var i = 0; i < untagged.length; i++) {

        untagged[i].addEventListener("click", function (e) {
            e = e || window.event;
            var target = e.target || e.srcElement;


            if (target.tagName === 'LABEL') {
                //console.log("target = label")

                if (target.classList.contains('tagged')) {
                    target.classList.remove('tagged');
                    target.classList.add('untagged')
                }
                else {
                    target.classList.remove('untagged');
                    target.classList.add('tagged')
                }
            }


        });
    }




}



function add_tag_start(string) {
    var target
    if (string == 'article-tag') {
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
                <button type="button" class="main-button cancel" onclick="add_tag_cancel('${target}')">Cancel</button>
            </div>
        </div>
    </form>
    `;
    var input = document.getElementById('add_tag_input');
    input.focus();
    // Execute a function when the user releases a key on the keyboard
    input.addEventListener("keyup", function (event) {
        // Number 13 is the "Enter" key on the keyboard
        if (event.keyCode === 13) {
            // Cancel the default action, if needed
            event.preventDefault();
            // Trigger the button element with a click
            document.getElementById("submit_new_tag").click();
        }
    });


}

function add_tag_cancel(string) {


    add.innerHTML = `
    <button id="add_new_button" onclick = "add_tag_start('${string}')" class = "main-button add_new">Add New</button>
    `;
}



function add_tag_finish(string) {
    var new_tag = document.getElementById('add_tag_input').value;

    if (new_tag == '') {
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

    new_label.addEventListener("click", function (e) {
        e = e || window.event;
        var target = e.target || e.srcElement;


        if (target.tagName === 'LABEL') {
            //console.log("target = label")

            if (target.classList.contains('tagged')) {
                target.classList.remove('tagged');
                target.classList.add('untagged')
            }
            else {
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

function article_updated(data) {
    var a = byId('articles_page');
    a.innerHTML = data;
    initialize();
}

function filter() {
    //console.log('filter()')
    var doc_tags = byClass('tagged');
    //console.log(doc_tags)
    var tags = []

    for (var i = 0; i < doc_tags.length; i++) {
        tags.push(doc_tags[i].firstElementChild.value);
    }

    data = {
        'tags': tags,
    }


    $.post('/app/articles/filter', {
        'data': JSON.stringify(data)
    }).done(function (data) {
        article_updated(data)
    });
}


function save(article_id) {

    var doc_tags, doc_remove_tags, tags, title, read_status, notes, content, data, reflections;

    //console.log('saving');

    doc_tags = byClass('tagged');
    doc_remove_tags = byClass('untagged');
    tags = [];
    remove_tags = [];
    if (doc_tags) {
        for (var i = 0; i < doc_tags.length; i++) {
            if (doc_tags[i].classList.contains('filter-tag') || doc_tags[i].classList.contains('new-article-tag')) {
                continue;
            }

            tags.push(doc_tags[i].firstElementChild.value);
        };
    }

    if (doc_remove_tags) {
        for (var i = 0; i < doc_remove_tags.length; i++) {
            if (doc_remove_tags[i].classList.contains('filter-tag') || doc_remove_tags[i].classList.contains('new-article-tag')) {
                continue;
            }
            remove_tags.push(doc_remove_tags[i].firstElementChild.value);
        };
    }



    title = byId('title_edit').value;
    read_status = byId('read_edit').value;

    notes = tinymce.get('notes_edit').getContent()
    if (byId('reflections_edit')) {
        reflections = tinymce.get('reflections_edit').getContent()
    }

    //console.log(notes)
    if (byId('content_edit')) {
        content = tinymce.get('content_edit').getContent()
    }

    //notes = byId('notes_edit').value;
    //content = byId('content_edit').value;

    data = {
        'title': title,
        'read_status': read_status,
        'notes': notes,
        'reflections': reflections,
        'content': content,
        'tags': tags,
        'remove_tags': remove_tags
    }


    $.post('/app/articles/' + article_id + '/update', {
        'data': JSON.stringify(data)
    }).done(function (data) {
        article_updated(data)
        initialize_articles_page()
    });

}



