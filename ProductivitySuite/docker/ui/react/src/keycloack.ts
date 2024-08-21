// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import Keycloak from "keycloak-js";
import { KEYCLOACK_SERVICE_URL } from "./config";
const keycloak = new Keycloak({
  url: KEYCLOACK_SERVICE_URL,
  realm: "productivitysuite",
  clientId: "productivitysuite",
});

export default keycloak;
