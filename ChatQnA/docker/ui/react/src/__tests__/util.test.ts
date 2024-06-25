// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { describe, expect, test } from "vitest";
import { getCurrentTimeStamp, uuidv4 } from "../common/util";

describe("unit tests", () => {
  test("check UUID is of length 36", () => {
    expect(uuidv4()).toHaveLength(36);
  });
  test("check TimeStamp generated is of unix", () => {
    expect(getCurrentTimeStamp()).toBe(Math.floor(Date.now() / 1000));
  });
});
