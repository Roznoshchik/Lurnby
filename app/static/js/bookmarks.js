var b_add = byId('bookmark-add');
var user_bookmarks = byId('user-bookmarks');

if( screen.width < 768){
    b_add.innerHTML = 'Add';
}

b_add.addEventListener('click', add_bookmark)


function add_bookmark(){
    if (byId('bookmark-name').value == ''){
        return
    }
    
    let x = get_location()
    user_bookmarks.innerHTML = user_bookmarks.innerHTML + `
    <div class="bookmark-row">
        <button class="bookmark-location" onclick="go_to_location(${x})">${byId('bookmark-name').value}</button>
        <button class="clear-button" onclick="delete_bookmark(this)">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-x" viewBox="0 0 16 16">
            <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
        </svg></button>
    </div>`;
    all_bookmarks[byId('bookmark-name').value] = x
    console.log(all_bookmarks)
    save_bookmarks();
    byId('bookmark-name').value = '';
}

function delete_bookmark(element){
    var target = element.parentElement;
    target.remove()
    let bk = target.firstElementChild.innerHTML;
    if (bk in all_bookmarks){
        delete all_bookmarks[bk]
    }

    save_bookmarks()
}

function go_to_location(location) { 
    // var $window = $(window);
    // console.log('going to location')
    // console.log(location)

    // var h = document.documentElement, 
    // b = document.body,
    // sh = 'scrollHeight';
    // var position = (location / 100) * (h[sh] || b[sh])    
    // $window.scrollTop(position);

    let docElem = document.documentElement,
        docBody = document.body,
        scrollBottom = (docElem['scrollHeight'] || docBody['scrollHeight']) - window.innerHeight,
        position = (location / 100) * scrollBottom
        $(window).scrollTop(position)

  };

function get_location(){
    // var h = document.documentElement, 
    // b = document.body,
    // st = 'scrollTop',
    // sh = 'scrollHeight';
    // return (h[st] || b[st]) / (h[sh] || b[sh]) * 100;

    let docElem = document.documentElement,
        docBody = document.body,
        scrollTop = docElem['scrollTop'] || docBody['scrollTop'],
        scrollBottom = (docElem['scrollHeight'] || docBody['scrollHeight']) - window.innerHeight,
        scrollPercent = scrollTop / scrollBottom;

        return scrollPercent * 100;

}

function save_bookmarks(){
    all_bookmarks['furthest'] = furthest
    let bookmarks = JSON.stringify(all_bookmarks);
    
    $.post(`/article/${uuid}/bookmarks`, {
        'bookmarks': bookmarks
      });    
}


function clear_furthest(){
    furthest = get_location();
    byId('furthest-read').onclick = function() {go_to_location(furthest)};
    save_bookmarks();
}


