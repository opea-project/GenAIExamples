import React from "react";
import { createRoot } from "react-dom/client";
import "./index.scss";
import App from "./App";
import { Provider } from "react-redux";
import { store } from "@redux/store";
import { ThemeProvider } from "@contexts/ThemeContext";
import keycloak from "@root/keycloak";
import { ReactKeycloakProvider } from "@react-keycloak/web";

const root = createRoot(document.getElementById("root")!);
root.render(
  //@ts-ignore
  <ReactKeycloakProvider
    authClient={keycloak}
    initOptions={{ onLoad: "login-required" }}
  >
    <Provider store={store}>
      <ThemeProvider>
        <App />
      </ThemeProvider>
    </Provider>
  </ReactKeycloakProvider>,
);
