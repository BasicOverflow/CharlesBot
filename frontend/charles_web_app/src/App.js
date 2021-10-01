import './App.css';
import Header from './components/header.js'
import Interface from './components/interface.js'
import { memo,useState,useEffect } from "react"

const ws = new WebSocket('ws://10.0.0.129:8004/ws/CommandSessionClient/WebClient')


function App() {
  console.log("app")
  const [connected, setConnected] = useState(false);

  ws.onopen = () => {
    if (connected === true) {
      console.log("Connection alread present, closing")
      ws.close()
    }
    else {
      setConnected(true);
      console.log('WebSocket Connected');
    }
    
  }
  ws.onclose = () => (setConnected(false));

  // useEffect(() => {
  //   return () => {
  //     // console.log("working")
  //     ws.close()
  //   }
  // }, [ws.onclose]);
  

  return (
    <div className="App">
        <Header/>
      <div className="showcase"> 
        <Interface ws={ ws }/> 
      </div>
    </div>
  );
}

export default memo(App);

