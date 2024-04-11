import "./app-header.scss";

import { NavLink } from "react-router-dom";

const AppHeader = () => {
  return (
    <header className="app-header">
      <img alt="Intel Logo" className="intel-logo" />
      <h3 className="app-title">Enhancing Generative AI – Business Relevant Results with RAG</h3>
      <nav>
        <NavLink to="/chat">Chat</NavLink>
        <NavLink to="/telemetry">Telemetry</NavLink>
      </nav>
    </header>
  );
};

export default AppHeader;
