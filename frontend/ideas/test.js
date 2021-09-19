// Upon the first submit: 
    // send post request to API, 
    // determine random port Here
    // create ws connection to that port on the server

    

function main(event){
    console.log(window.location.href)
    event.preventDefault();
    post_command(event);
    start_ws_conn(event);
}



function post_command(event){
    event.preventDefault()
    const input = document.getElementById("messageText");
    //make fetchapi post request
    fetch(`http://10.0.0.129:8004/webShip/${input.value}`, {
    method: 'POST', // or 'PUT'
    headers: {
        'Content-Type': 'application/json',
        'mode': 'no-cors'
    },
    body: JSON.stringify(input),
    })
}

function start_ws_conn(){
    var ws = new WebSocket("ws://10.0.0.129:8080");
    ws.onmessage = (event) => {
        // console.log(event.data);
        var messages = document.getElementById('messages')
        var message = document.createElement('li')
        var content = document.createTextNode(event.data)
        message.appendChild(content)
        messages.appendChild(message)
    };

    function sendMessage(event) {
        event.preventDefault()
        var input = document.getElementById("messageText")
        ws.send(input.value)
        input.value = ''
    }
}







