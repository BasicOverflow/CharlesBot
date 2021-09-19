// import { useState } from "react"



const Webship = ({ setShiped, setFirstMsg, firstMsg }) => {
    //upon sending ship request and receiving the successful confimation back, sets shipped bool in interface component to true so the chatlog can get rendered instead
    //when buttun is clicked, will call setShipped and fetch a post to the charles API

    const shipCmd = (command) => {
        //make post request to API 
        fetch(`http://10.0.0.129:8004/manualShip/WebClient/${command}`, {
            method: 'POST',
            headers: {
                'accept': 'application/json',
                'mode': 'no-cors'
            }
        }).then(function(res){ return res.json(); })
        .then(function(data){ console.log( JSON.stringify(data)) })
    }

    const getInptVal = (e) => {
        // console.log(e.target.value);
        // setFirstMsg({ from:'client', content:e.target.value });
        setFirstMsg(e.target.value);
    }

    return (
        <div className="container">
            <h1>Ship Command</h1>
            <input type="text" id="messageText" onChange={ getInptVal }/>
            <button onClick={() => {
                shipCmd(firstMsg);
                setShiped();
            }
            }>Send</button>
        </div>
    )
}

export default Webship