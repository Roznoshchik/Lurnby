
tos_modal = byId('tos_modal')
see_terms = byId('see_terms')
auth_welcome = byId('auth_tos_welcome')
auth_terms = byId('auth_terms')
auth_tos = byId('auth_tos')
auth_accept = byId('auth_accept')
auth_decline = byId('auth_decline')


function lurnby_terms(action){
    url = '/app/legal/accept_terms'
    if(action == 'see_terms'){
        fetch(url, {
            method: 'get',
            headers: {
                'Content-type': 'application/html',
                'X-CSRFToken': csrf_token
            }
        })
        .then(response => response.json())
        .then(data => {
            tos_modal.innerHTML = data['html']
            accept_terms = byId('accept_terms')
            decline_terms = byId('decline_terms')   

            decline_terms.addEventListener('click', function(){
                lurnby_terms('decline_terms')
            })
            
            accept_terms.addEventListener('click', function(){
                lurnby_terms('accept_terms')
            })

        })
    }
    else {
        fetch(url, {
            method: 'POST', 
            headers: {
                'Content-type': 'application/html',
                'X-CSRFToken': csrf_token
            },
            body: JSON.stringify({'action': action})
        })
        .then(response => response.json())
        .then(data => {
            if (data['accepted']){
                tos_modal.style.display = "none"
                window.location.reload()
            }
            else{
                window.location.href = '/app/settings/account'
            }
        })
    }
}

if (see_terms){
    see_terms.addEventListener('click', function(){
        lurnby_terms('see_terms')
    });
}


if(auth_terms){
    auth_terms.addEventListener('click', function(){
        console.log('clickedd auth terms button')
        auth_welcome.style.display = "none"
        auth_tos.style.display = "block"
        auth_terms.style.display="none"
        auth_accept.style.display="block"
        auth_decline.style.display="block"
    })
}
