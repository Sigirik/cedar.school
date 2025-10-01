// import { useState } from "react";
// import ExcalidrawBoard from "./ExcalidrawBoard";
// import JitsiEmbed from "./JitsiEmbed";

export default function LiveLessonDemo() {
  // const [roomName] = useState("cedar-demo-room");
  // const [username] = useState("User"); // можно заменить на авторизованного
  // const [canEdit] = useState(true); // всегда разрешено редактировать

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      <div style={{ flex: 1, display: "flex", flexDirection: "row" }}>
        <div style={{ flex: 1, borderRight: "2px solid #ccc" }}>
          {/* <JitsiEmbed roomName={roomName} userName={username} /> */}
        </div>
        <div style={{ flex: 1 }}>
          {/* <ExcalidrawBoard
            roomName={roomName}
            userName={username}
            canEdit={canEdit}
          /> */}
        </div>
      </div>
    </div>
  );
}
