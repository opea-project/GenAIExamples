//@ts-ignore
import Keycloak from "keycloak-js";

import { KEYCLOAK_SERVICE_URL } from "@root/config";

const keyCloakConfig = {
    url: KEYCLOAK_SERVICE_URL,
    realm: "productivitysuite",
    clientId: "productivitysuite",
}

const keycloak = new Keycloak(keyCloakConfig);

export default keycloak;
