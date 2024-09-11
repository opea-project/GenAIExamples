// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import ReactDOM from "react-dom/client"
import App from "./App.tsx"
import "./index.scss"
import { Provider } from 'react-redux'
import { store } from "./redux/store.ts"
import keycloak from "./keycloack.ts"
import { ReactKeycloakProvider } from "@react-keycloak/web";



ReactDOM.createRoot(document.getElementById("root")!).render(
  <>
    <ReactKeycloakProvider authClient={keycloak} initOptions={ {onLoad:'login-required'}}>
    <Provider store={store} >
      <App />
    </Provider>
    </ReactKeycloakProvider>
  </>
)
