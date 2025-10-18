# Setup Scripts for Webarena

We will launch a shopping admin website, part of [WebArena](https://github.com/web-arena-x/webarena), to serve as a web server for agent evaluation. The deployment process will follow the instructions in the [webarena-setup](https://github.com/gasse/webarena-setup) repository.

## Download Docker Image

1. Download shopping_admin_final_0719.tar from the [official webarena repo](https://github.com/web-arena-x/webarena/tree/main/environment_docker).

2. Place the archive file, shopping_admin_final_0719.tar, into the directory specified by the `ARCHIVES_LOCATION` parameter within `tests/webarena/set_env.sh`

## Launch the Web Site

Please ensure Docker services work in your environment, and perform the following command to launch the web site:

```bash
bash shopping_admin.sh start
```

## Stop the Web Site

```bash
bash shopping_admin.sh stop
```
