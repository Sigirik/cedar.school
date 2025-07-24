import React, { useRef, useEffect, useState } from "react";
import { Excalidraw, ExcalidrawImperativeAPI } from "@excalidraw/excalidraw";
import '@/styles/excalidraw.css';

type Props = {
  canEdit: boolean;
  role: "teacher" | "student";
};

const ExcalidrawBoard: React.FC<Props> = ({ canEdit, role }) => {
  const excalidrawRef = useRef<ExcalidrawImperativeAPI>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setMounted(true), 100);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (excalidrawRef.current) {
      excalidrawRef.current.updateScene({
        appState: {
          viewModeEnabled: !canEdit,
        },
      });
    }
  }, [canEdit]);

  if (!mounted) return null;

  return (
    <div style={{ height: "100%", width: "100%", position: "relative" }}>
      {role === "student" && canEdit && (
        <div
          style={{
            position: "absolute",
            top: 10,
            left: 10,
            background: "#e6ffed",
            border: "1px solid #2ecc71",
            padding: "8px 12px",
            borderRadius: "6px",
            zIndex: 10,
            color: "#2c662d",
            fontWeight: 500,
          }}
        >
          ✅ Учитель дал вам доступ к доске
        </div>
      )}
      <Excalidraw ref={excalidrawRef} />
    </div>
  );
};


export default ExcalidrawBoard;

