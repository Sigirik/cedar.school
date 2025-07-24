import React from "react";

type Props = {
  roomName: string;
  displayName: string;
};

const JitsiEmbed: React.FC<Props> = ({ roomName, displayName }) => {
  const url = `https://meet.jit.si/${roomName}#userInfo.displayName=${displayName}`;
  return (
    <iframe
      src={url}
      allow="camera; microphone; fullscreen; display-capture"
      className="w-full h-full border-0"
      title="Jitsi Room"
    />
  );
};

export default JitsiEmbed;
