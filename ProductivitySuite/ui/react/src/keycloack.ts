// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import Keycloak from "keycloak-js";
import { KEYCLOACK_SERVICE_URL } from "./config";
const keycloak = new Keycloak({
  url: KEYCLOACK_SERVICE_URL,
  realm: "productivitysuite",
  clientId: "productivitysuite",
});

//auto refresh access token when expired
keycloak.onTokenExpired = async () => {
  console.log("token expired", keycloak.token);
  await keycloak.updateToken(30);
};

export default keycloak;
