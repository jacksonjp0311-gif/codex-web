import React from "react";
import CreativeChatBox from "./CreativeChatBox";

export default function CodePane({ file, patches, onRequest }) {
  return (
    <div>
      <h4>{file.path}</h4>
      <pre>{file.content}</pre>
      <CreativeChatBox 
        context={file.content} 
        onRequest={opts=>onRequest(file.path, opts)} 
      />
      <ul>
        {patches.map((p,i)=><li key={i}><pre>{p.diff}</pre></li>)}
      </ul>
    </div>
  );
}
