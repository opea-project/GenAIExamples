# Keycloak Configuration Setup

This document show you step-by-step how to configure Keycloak settings.

The user management is done via Keycloak and the configuration steps look like this:

1. Access the Keycloak admin console via url http:${host_ip}:8080 or endpoint that exposed from your kubernetes cluster to configure user. Use default username(admin) and password(admin) to login.
   ![project-screenshot](../../assets/img/keycloak_login.png)
2. Create a new realm named **productivitysuite** within Keycloak.
   ![project-screenshot](../../assets/img/create_realm.png)
   ![project-screenshot](../../assets/img/create_productivitysuite_realm.png)
3. Create a new client called **productivitysuite** with default configurations.
   ![project-screenshot](../../assets/img/create_client.png)
4. Select the **productivitysuite** client that created just now. Insert your ProductivitySuite UI url endpoint into "Valid redirect URIs" and "Web origins" field. Example as screenshot below:
   ![project-screenshot](../../assets/img/productivitysuite_client_settings.png)
5. From the left pane select the Realm roles and create a new role name as user and another new role as viewer.
   ![project-screenshot](../../assets/img/create_roles.png)
6. Create a new user name as for example mary and another user as bob. Set passwords for both users (set 'Temporary' to 'Off'). Select Role mapping on the top, assign the user role to mary and assign the viewer role to bob.
   ![project-screenshot](../../assets/img/create_users.png)
   ![project-screenshot](../../assets/img/set_user_password.png)
   ![project-screenshot](../../assets/img/user_role_mapping.png)
