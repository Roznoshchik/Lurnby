var menu = byId('settings_menu')

var move = (menu.scrollWidth - menu.clientWidth) / 2 

var left = byClass('nav_left')[0]
var right = byClass('nav_right')[0]

left.addEventListener('click', () => {menu.scrollLeft -= move} )
right.addEventListener('click', () => {menu.scrollLeft += move} )

function button_viz(){
    // if (menu.scrollLeft == 0) {
    //     left.style.display = "none"
    //     right.style.display = "block"
    // }
    // else if(menu.scrollLeft == menu.scrollWidth - menu.clientWidth){
    //     left.style.display = "block"
    //     right.style.display = "none"
    // }
    // else {
    //     left.style.display = "block"
    //     right.style.display = "block"
    // }

    if (menu.scrollLeft == 0) {
        left.style.opacity = 0
        right.style.opacity = 100
    }
    else if(menu.scrollLeft == menu.scrollWidth - menu.clientWidth){
        left.style.opacity = 100
        right.style.opacity = 0
    }
    else {
        left.style.opacity = 100
        right.style.opacity = 100
    }



}

menu.addEventListener('scroll', () => {button_viz()})