//////////////////////
//                  //
//   Autocomplete   //
//                  //
//////////////////////


function autocomplete(inp, arr, create=false) {
    /*the autocomplete function takes two arguments,
    the text field element and an array of possible autocompleted values:*/
    var currentFocus;

    function create_list(val, parent, id){
        var a, b, i
        currentFocus = -1;
        /*create a DIV element that will contain the items (values):*/
        a = document.createElement("DIV");
        a.setAttribute("id", id + "autocomplete-list");
        a.setAttribute("class", "autocomplete-items");
        /*append the DIV element as a child of the autocomplete container:*/
        parent.appendChild(a);
        /*for each item in the array...*/
        exact_match=false
        for (i = 0; i < arr.length; i++) {
            var x = arr[i]
            if (val){
                if (arr[i].toUpperCase().includes(val.toUpperCase())){
                    if(arr[i].toUpperCase() === val.toUpperCase()){
                        exact_match=true
                    }
                }
                else{
                    continue;
                }
            }
            /*create a DIV element for each matching element:*/
            b = document.createElement("DIV");
            /*insert a input field that will hold the current array item's value:*/
            b.innerHTML = x
            /*execute a function when someone clicks on the item value (DIV element):*/
            b.addEventListener("click", function(e) {
                e=e || window.event;
                var elem = e.target || e.srcElement;
                if (create){
                    t = make_topic_span(elem.innerHTML, ['topic', 'member'])
                    byId('Members').appendChild(t)
                        
                    byId('topic_input').value = ''
                    byId('topic_input').focus()

                }
                else{
                    /*insert the value for the autocomplete text field:*/
                    if (!filters.includes(elem.innerHTML)){
                        filters.push(elem.innerHTML)
                        t = make_topic_span(elem.innerHTML, ['topic', 'filter'])
                        active_filters.appendChild(t)
                        
                        byId('filter_input').value = ''
                        byId('filter_input').focus()
                    }
                }
            
            
                /*close the list of autocompleted values,
                (or any other open lists of autocompleted values:*/
                closeAllLists();
            });
            a.appendChild(b);
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

        // if (!val) { return false;}
        currentFocus = -1;
        // /*create a DIV element that will contain the items (values):*/
        // a = document.createElement("DIV");
        // a.setAttribute("id", this.id + "autocomplete-list");
        // a.setAttribute("class", "autocomplete-items");
        // /*append the DIV element as a child of the autocomplete container:*/
        // this.parentNode.appendChild(a);
        // /*for each item in the array...*/
        // exact_match=false
        // for (i = 0; i < arr.length; i++) {
        //     var x = arr[i]
        //     /*check if the item starts with the same letters as the text field value:*/
        //     if (arr[i].toUpperCase().includes(val.toUpperCase())){
        //         if(arr[i].toUpperCase() === val.toUpperCase()){
        //             exact_match=true
        //         }
        //         /*create a DIV element for each matching element:*/
        //         b = document.createElement("DIV");
        //         /*insert a input field that will hold the current array item's value:*/
        //         b.innerHTML = x
        //         /*execute a function when someone clicks on the item value (DIV element):*/
        //         b.addEventListener("click", function(e) {
        //             e=e || window.event;
        //             var elem = e.target || e.srcElement;
        //             if (create){
        //                 t = make_topic_span(elem.innerHTML, ['topic', 'member'])
        //                 byId('Members').appendChild(t)
                            
        //                 byId('topic_input').value = ''
        //                 byId('topic_input').focus()

        //             }
        //             else{
        //                 /*insert the value for the autocomplete text field:*/
        //                 if (!filters.includes(elem.innerHTML)){
        //                     filters.push(elem.innerHTML)
        //                     t = make_topic_span(elem.innerHTML, ['topic', 'filter'])
        //                     active_filters.appendChild(t)
                            
        //                     byId('filter_input').value = ''
        //                     byId('filter_input').focus()
        //                 }
        //             }
                
                
        //             /*close the list of autocompleted values,
        //             (or any other open lists of autocompleted values:*/
        //             closeAllLists();
        //         });
        //         a.appendChild(b);
        //     }
        // }
        if (create){
            // if match was found
            if(!exact_match){
                // offer to create a topic with the input
                /*create a DIV element for each matching element:*/
                b = document.createElement("DIV");
                /*insert a input field that will hold the current array item's value:*/
                b.innerHTML = `Click to create topic: ${inp.value}`
                /*execute a function when someone clicks on the item value (DIV element):*/
                b.addEventListener("click", function(e) {
                    e=e || window.event;
                    var elem = e.target || e.srcElement;
                    
                    t = make_topic_span(inp.value, ['topic', 'member'])
                    byId('Members').appendChild(t)
                        
                    byId('topic_input').value = ''
                    byId('topic_input').focus()
                    
                
                    /*close the list of autocompleted values,
                    (or any other open lists of autocompleted values:*/
                    closeAllLists();
                });
                a.appendChild(b);
            }
        }
        
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
            t.id = 'member-topic'+topic_title
        }
        else{
            t.id = 'topic'+topic_title
        }
        t.addEventListener('click', function(e){
            e=e || window.event;
            var target = e.target || e.srcElement;
            if (!create){
                var rem = target.id.slice(5)
                filters = filters.filter(elem => elem !== rem); 
            }
            byId(target.id).remove()
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

    function closeAllLists(elmnt) {
        /*close all autocomplete lists in the document,
        except the one passed as an argument:*/
        var x = document.getElementsByClassName("autocomplete-items");
        var inp1 = byId('filter_input'), inp2 = byId("topic_input")
        for (var i = 0; i < x.length; i++) {
            if (elmnt != inp2 && elmnt != inp1 && elmnt != x[i]) {
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