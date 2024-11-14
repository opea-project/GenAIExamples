# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Use node 20.11.1 as the base image
FROM node:20.11.1

# Update package manager and install Git
RUN apt-get update -y && apt-get install -y git

# Copy the front-end code repository
COPY svelte /home/user/svelte

# Set the working directory
WORKDIR /home/user/svelte

# Install front-end dependencies
RUN npm install

# Build the front-end application
RUN npm run build

# Expose the port of the front-end application
EXPOSE 5173

# Run the front-end application in preview mode
CMD ["npm", "run", "preview", "--", "--port", "5173", "--host", "0.0.0.0"]
