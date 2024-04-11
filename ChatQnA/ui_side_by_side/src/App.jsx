import { useEffect } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import AppHeader from "./layout/app-header/AppHeader";
import ChatPage from "./pages/chat/ChatPage";
import TelemetryPage from "./pages/telemetry/TelemetryPage";

const App = () => {
  useEffect(() => {
    localStorage.clear();
  }, []);

  return (
    <BrowserRouter>
      <AppHeader />
      <Routes>
        <Route path="/" element={<Navigate to="/chat" />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="telemetry" element={<TelemetryPage />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
