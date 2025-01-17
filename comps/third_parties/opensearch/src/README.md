# Start Opensearch server

## Prerequisites

1. Install docker
1. Install docker compose (if not already installed)
   1. `sudo curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose`
   2. `sudo chmod +x /usr/local/bin/docker-compose`

## Instructions

### 1. Set admin password as environment variable

OpenSearch version 2.12 and later require a custom admin password to be set. Following [these guidelines](https://opensearch.org/docs/latest/security/configuration/demo-configuration/#setting-up-a-custom-admin-password), set the admin password as an environment variable to be used by the `docker-compose-opensearch.yml` file like `export OPENSEARCH_INITIAL_ADMIN_PASSWORD=_some_admin_password` in the terminal before starting the docker containers.

### 2. Start the cluster

`docker-compose -f docker-compose-opensearch.yml up`

## Troubleshooting

### "java.nio.file.FileSystemNotFoundException: null" error

1. Make sure to grant read permissions to your local data volume folders
   1. `sudo chown -R instance_user:instance_user ./opensearch-data1`
   2. `sudo chown -R instance_user:instance_user ./opensearch-data2`
      1. Replace `instance_user` with the login user (i.e. ec2-user, ssm-user, or your local user name)
2. Try increasing the virtual max memory map count
   1. `sudo sysctl -w vm.max_map_count=262144`

### OpenSearch Dashboards container errors

1. Make sure to grant read permission to the `opensearch_dashboards.yml` file
1. `sudo chown -R instance_user:instance_user ./opensearch_dashboards.yml`
   1. Replace `instance_user` with the login user (i.e. ec2-user, ssm-user, or your local user name)
