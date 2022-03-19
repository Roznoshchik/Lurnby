//////////////////////
//                  //
//   Autocomplete   //
//                  //
//////////////////////


function autocomplete(inp, arr, dest, create=false, location) {

    /*the autocomplete function takes two arguments,
    the text field element and an array of possible autocompleted values:*/
    var currentFocus;

    function create_list(val, parent, id){
        var a, b, c, i
        currentFocus = -1;
        
        /*create a DIV element that will contain the items (values):*/
        a = document.createElement("DIV");
        a.setAttribute("id", id + "autocomplete-list");
        a.setAttribute("class", "autocomplete-items");
        
        /*append the DIV element as a child of the autocomplete container:*/
        parent.appendChild(a);
        
        /*for each item in the array check to see if it includes the value and if it is also 
        an exact match for the value then also set exact_match to be true....*/
        exact_match=false
        for (i = 0; i < arr.length; i++) {
            var x = arr[i]
            if (val){
                if (arr[i].toUpperCase().includes(val.toUpperCase())){
                    if(arr[i].toUpperCase() === val.toUpperCase()){
                        exact_match=true
                    }
                }
                else {
                    continue;
                }
            }  
            /*create a DIV element for each matching element:*/
            b = document.createElement("DIV");
            
            /*insert a input field that will hold the current array item's value:*/
            b.innerHTML = x
            
            /*execute a function when someone clicks on the item value (DIV element):*/
            b.addEventListener("click", function(e, loc=location) {
                e=e || window.event;
                var elem = e.target || e.srcElement;
                

                if (loc == 'viewhighlight'){
                    t = make_topic_span(elem.innerHTML, ['topic', 'member'])
                }
                else if(loc == 'addhighlight'){
                    t = make_topic_span(elem.innerHTML, ['topic', 'add_highlight_member'])
                }
                else if(loc == 'filterhighlight'){
                    t = make_topic_span(elem.innerHTML, ['topic', 'filter_highlight_member'])
                }
                else if(loc == 'FinishArticleModal'){
                    t = make_topic_span(elem.innerHTML, ['topic', 'tagMember'])
                }

                dest.appendChild(t)
            
                // find the index of this tag and remove it from the nonmember list
                let start = arr.indexOf(elem.innerHTML);
                arr.splice(start, 1);
                    
                   
                inp.value = ''
                inp.focus()
                create_list('', parent, id)
                
                /*close the list of autocompleted values,
                (or any other open lists of autocompleted values:*/
                closeAllLists();
            });
            a.appendChild(b);
        }
        // if we are in the update or creating topic space
        if (create){
            // if no match was found
            if(!exact_match && inp.value != ''){
                // offer to create a topic with the input
                
                /*create a DIV element for each matching element:*/
                c = document.createElement("DIV");
                
                /*insert a input field that will hold the current array item's value:*/
                c.innerHTML = `Click to create topic: ${inp.value}`
                
                /*execute a function when someone clicks on the item value (DIV element):*/
                c.addEventListener("click", function(e, loc=location) {
                    e=e || window.event;
                    var elem = e.target || e.srcElement;

                    if (loc == 'viewhighlight'){
                        t = make_topic_span(inp.value, ['topic', 'member'])
                    }
                    else if(loc == 'addhighlight'){
                        t = make_topic_span(inp.value, ['topic', 'add_highlight_member'])
                    }
                    else if(loc == 'FinishArticleModal'){
                        t = make_topic_span(inp.value, ['topic', 'tagMember'])
                    }
                
                    dest.appendChild(t)

                    // byId('topic_input').value = ''
                    // byId('topic_input').focus()

                    inp.value = ''
                    inp.focus()
                    create_list('', parent, id)


                    /*close the list of autocompleted values,
                    (or any other open lists of autocompleted values:*/
                    closeAllLists();
                });
                a.appendChild(c);
            }
        }
    }


    inp.addEventListener("focus", function(e){
        val = this.value;
        parent = this.parentNode
        id = this.id
        /*close any already open lists of autocompleted values*/
        closeAllLists();
        create_list(val, parent, id)
    });

    /*execute a function when someone writes in the text field:*/
    inp.addEventListener("input", function(e) {
        var val = this.value, parent = this.parentNode, id=this.id;
        /*close any already open lists of autocompleted values*/
        closeAllLists();
        create_list(val, parent, id)
        currentFocus = -1;

    });

    
    /*execute a function presses a key on the keyboard:*/
    inp.addEventListener("keydown", function(e) {
        var x = document.getElementById(this.id + "autocomplete-list");
        if (x) x = x.getElementsByTagName("div");
        if (e.keyCode == 40) {
            /*If the arrow DOWN key is pressed,
            
            increase the currentFocus variable:*/
            currentFocus++;
           
            /*and and make the current item more visible:*/
            addActive(x);
        } else if (e.keyCode == 38) { //up
            /*If the arrow UP key is pressed,
            decrease the currentFocus variable:*/
            currentFocus--;
            /*and and make the current item more visible:*/
            addActive(x);
        } else if (e.keyCode == 13) {
            /*If the ENTER key is pressed, prevent the form from being submitted,*/
            e.preventDefault();
            if (currentFocus > -1) {
            /*and simulate a click on the "active" item:*/
            if (x) x[currentFocus].click();
            }
            create_list(val, parent, id)

        }
    });

    // These functions need to be inside of the autocomplete function
    // because they use the inp and create variable
    function make_topic_span(topic_title, classlist){
        t = document.createElement('span')
        for (var i=0; i < classlist.length; i++){
            t.classList.add(classlist[i])
        }
        t.innerHTML = topic_title
        if(create){
            if (location == 'FinishArticleModal'){
                t.id = 'member-tag'+topic_title
            }
            else{
                t.id = 'member-topic'+topic_title
            }
        }
        else{
            t.id = 'topic'+topic_title
        }
        t.addEventListener('click', function(e){
            e=e || window.event;
            var target = e.target || e.srcElement;
            //byId(target.id).remove()
            this.remove()
            arr.push(topic_title)
        })

        return t
    }


    function addActive(x) {
        /*a function to classify an item as "active":*/
        if (!x) {return false};
        /*start by removing the "active" class on all items:*/
        removeActive(x);
        if (currentFocus >= x.length) {currentFocus = 0};
        if (currentFocus < 0) {currentFocus = (x.length - 1)};
        /*add class "autocomplete-active":*/
        x[currentFocus].classList.add("autocomplete-active");
    }

    function removeActive(x) {
        /*a function to remove the "active" class from all autocomplete items:*/
        for (var i = 0; i < x.length; i++) {
            x[i].classList.remove("autocomplete-active");
        }
    }

    function closeAllLists(elmnt=null) {
        /*close all autocomplete lists in the document,
        except the one passed as an argument:*/
        var x = document.getElementsByClassName("autocomplete-items");
        var inp1 = byId('filter_input'), inp2 = byId("topic_input"), inp3 = byId("new_highlight_topic_input"), inp4 = byId('tag_input')
        for (var i = 0; i < x.length; i++) {
            if (elmnt != inp2 && elmnt != inp1 && elmnt != inp3 && elmnt != inp4) {
                x[i].parentNode.removeChild(x[i]);
            }
            else if(elmnt == null){
                x[i].parentNode.removeChild(x[i]);
            }
        }
    }

    /*execute a function when someone clicks in the document:*/
    document.addEventListener("click", function (e) {
        if (!e.target.classList.contains('autocomplete-items')){
            closeAllLists(e.target);
        }
    });
}