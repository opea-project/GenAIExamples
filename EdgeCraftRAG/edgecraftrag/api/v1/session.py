# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from edgecraftrag.api_schema import SessionIn
from edgecraftrag.context import ctx
from fastapi import FastAPI

session_app = FastAPI()


@session_app.get("/v1/sessions")
def get_all_sessions():
    return ctx.get_session_mgr().get_all_sessions()


@session_app.get("/v1/session/{idx}")
def get_session_by_id(idx: str):
    content = ctx.get_session_mgr().get_session_by_id(idx)
    return {"session_id": idx, "session_content": content}
