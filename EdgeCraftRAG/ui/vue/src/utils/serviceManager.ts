// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

type ServiceMap = {
  antNotification: (type: "success" | "warning" | "error" | "info", message: string, description?: string) => void;
};

class ServiceManager {
  private static instance: ServiceManager;
  private services: { [P in keyof ServiceMap]?: ServiceMap[P] } = {};

  private constructor() {}

  public static getInstance(): ServiceManager {
    if (!ServiceManager.instance) {
      ServiceManager.instance = new ServiceManager();
    }
    return ServiceManager.instance;
  }

  public registerService<K extends keyof ServiceMap>(name: K, service: ServiceMap[K]): void {
    this.services[name] = service;
  }

  public getService<K extends keyof ServiceMap>(name: K): ServiceMap[K] | undefined {
    return this.services[name];
  }
}

export default ServiceManager.getInstance();
