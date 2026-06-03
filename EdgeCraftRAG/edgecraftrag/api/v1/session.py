# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from edgecraftrag.context import ctx
from fastapi import FastAPI, HTTPException, status

session_app = FastAPI()


@session_app.get("/v1/sessions")
def get_all_sessions():
    return ctx.get_session_mgr().get_all_sessions()


@session_app.get("/v1/session/{idx}")
def get_session_by_id(idx: str):
    content = ctx.get_session_mgr().get_session_by_id(idx)
    return {"session_id": idx, "session_content": content}


@session_app.delete("/v1/session/{idx}")
def delete_session_by_id(idx: str):
    try:
        deleted = ctx.get_session_mgr().delete_session_by_id(idx)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {idx} not found")
        return {"detail": f"Session {idx} deleted successfully"}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
