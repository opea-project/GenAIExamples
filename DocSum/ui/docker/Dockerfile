# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Use node 20.11.1 as the base image
FROM node:20.11.1 as svelte-base

# Update package manager and install Git and nginx
RUN apt-get update -y && apt-get install -y git

# Copy the front-end code repository
COPY svelte /home/user/svelte

# Set the working directory
WORKDIR /home/user/svelte

# Install front-end dependencies
RUN npm install

# Build the front-end application
RUN npm run build

FROM node:20.11.1 as svelte-server

RUN apt-get update -y && apt-get install -y nginx gettext

COPY --from=svelte-base /home/user/svelte/build /home/user/svelte/build
COPY --from=svelte-base /home/user/svelte/package.json /home/user/svelte

WORKDIR /home/user/svelte

RUN npm install --omit=dev

COPY ./svelte/nginx.conf /tmp/nginx.conf

ENTRYPOINT ["sh", "-c", "envsubst < /tmp/nginx.conf > /etc/nginx/conf.d/default.conf && /usr/sbin/nginx && node /home/user/svelte/build/index.js"]


# Use node 20.11.1 as the base image
FROM node:20.11.1 as react-base

COPY ./react /usr/app/react
WORKDIR /usr/app/react

RUN ["npm", "install"]
RUN ["npm", "run", "build"]


FROM nginx:alpine as react-server

COPY --from=react-base /usr/app/react/dist /usr/share/nginx/html

COPY ./react/nginx.conf /tmp/nginx.conf
ENTRYPOINT ["sh", "-c", "envsubst < /tmp/nginx.conf > /etc/nginx/conf.d/default.conf && /usr/sbin/nginx -g 'daemon off;'"]
