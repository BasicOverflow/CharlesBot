//the component that houses the actial communication with charles API
import { useState } from "react"
import Webship from "./webShip"
import ChatLog from "./chatlog"


//First renders webship
//once user inputs to ship a command to charles, the shipped bool is set to true and the chatlog will get rendered instead
//shipped is changed by the webship component by passing in a setShipped function as a prop

const Interface = ({ ws }) => {
    const [shipped, setShipped] = useState(false);
    const [firstMsg, setFirstMsg] = useState("");

    return (
        <div className="container">
            { shipped ? <ChatLog firstMsg={ firstMsg } ws={ ws } setShipped={ () => {setShipped(false)} }/> : 
            <Webship firstMsg={ firstMsg } setFirstMsg={ setFirstMsg } setShiped={ () => {setShipped(true);}}/> }
        </div>
    )
}

export default Interface











