import React from "react";

export default function ApprovalTab({ suggestions, onApprove, onDeny }) {
  return (
    <div>
      {suggestions.map((s,i)=>(
        <div key={i}>
          <pre>{s.diff}</pre>
          <button onClick={()=>onApprove(i)}>Approve</button>
          <button onClick={()=>onDeny(i)}>Deny</button>
        </div>
      ))}
      {suggestions.length>1 && 
        <button onClick={()=>onApprove("all")}>Approve All</button>
      }
    </div>
  );
}
