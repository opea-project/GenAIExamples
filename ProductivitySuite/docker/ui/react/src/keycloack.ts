import Keycloak from "keycloak-js";
import { KEYCLOACK_SERVICE_URL } from "./config";
console.log(KEYCLOACK_SERVICE_URL);
const keycloak = new Keycloak({
  url: KEYCLOACK_SERVICE_URL,
  realm: "istio",
  clientId: "istio",
});

export default keycloak;
