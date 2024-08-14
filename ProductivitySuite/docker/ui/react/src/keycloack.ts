import Keycloak from "keycloak-js";
import { KEYCLOACK_SERVICE_URL } from "./config";
const keycloak = new Keycloak({
  url: KEYCLOACK_SERVICE_URL,
  realm: "istio",
  clientId: "istio",
});

export default keycloak;
