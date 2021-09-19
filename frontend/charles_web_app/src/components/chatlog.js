import { useState } from 'react'
import { v4 as uuid } from 'uuid'


//https://scriptverse.academy/tutorials/reactjs-chat-websocket.html



//TODO: pass in props needed for starting websocket stream
const ChatLog = ({ firstMsg, ws, setShipped}) => {
    // messages is an array that holds all messages between user and charles. Schema for each msg: {"from":"", "content":""} *from user or charles
	const [messages, setMsgs] = useState([{ from:'client',content:firstMsg }]);
    const [message, setMessage] = useState([]);
	const [goBack, setGoBack] = useState(false);
	

    const submitMsg = (msg) => {
        const message = { from: "WebClient", content: msg };
        ws.send(message.content);
        setMsgs([...messages, message])
    }

	ws.onmessage = (e) => {
		const message = { from: "WebClient", content: e.data };
		setMsgs([...messages, message]);
		console.log(e.data);
		//TODO: Additional logic to detect charles sending to msges at once
		//Logic to detect end of command session:
		if (e.data.toLowerCase().includes("command completed")) {
			setGoBack(true);
		}

	}

	ws.onclose = () => {
		ws.close()
		console.log('WebSocket Disconnected');
	}

    return (
        <div className="container">
            <form
	          action=""
	          onSubmit={e => {
	            e.preventDefault();
	            submitMsg(message);
                setMessage([]);
	          }}
	        >
	          <input
	            type="text"
	            placeholder={'Type a message ...'}
	            value={message}
	            onChange={e => setMessage(e.target.value)}
	          />
	          <input type="submit" value={'Send'} />
	        </form>

            { messages.map( (msg) => (<h3 key={uuid()}>{ msg.content }</h3>)) }

			{ goBack ? <button onClick={() => { setShipped() }}>Go Back?</button>: <></> }

        </div>
    )
}

export default ChatLog




