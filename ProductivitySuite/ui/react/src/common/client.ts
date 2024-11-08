// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import axios from "axios";
import keycloak from "../keycloack";

//add iterceptors to add any request headers
axios.interceptors.request.use(async (config) => {
    config.headers['Authorization'] = `Bearer ${keycloak.token}`;
    return config;
});

export default axios;
