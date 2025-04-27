from typing import Optional
import aiohttp
import logging
from aiocache import cached
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel

from open_webui.config import (
    ENABLE_OPENROUTER_API,
    OPENROUTER_API_BASE_URLS,
    OPENROUTER_API_KEYS,
    OPENROUTER_API_CONFIGS,
)
from open_webui.env import (
    AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST,
    ENABLE_FORWARD_USER_INFO_HEADERS,
    BYPASS_MODEL_ACCESS_CONTROL,
)
from open_webui.models.users import UserModel
from open_webui.utils.auth import get_verified_user, get_admin_user
from open_webui.constants import ERROR_MESSAGES

log = logging.getLogger(__name__)
router = APIRouter()

async def send_get_request(url: str, key: Optional[str] = None, user: UserModel = None):
    timeout = aiohttp.ClientTimeout(total=AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST)
    try:
        async with aiohttp.ClientSession(timeout=timeout, trust_env=True) as session:
            async with session.get(
                f"{url}/models",
                headers={
                    **({"Authorization": f"Bearer {key}"} if key else {}),
                    **(
                        {
                            "X-OpenWebUI-User-Name": user.name,
                            "X-OpenWebUI-User-Id": user.id,
                            "X-OpenWebUI-User-Email": user.email,
                            "X-OpenWebUI-User-Role": user.role,
                        }
                        if ENABLE_FORWARD_USER_INFO_HEADERS and user
                        else {}
                    ),
                },
            ) as response:
                data = await response.json()
                if response.status != 200:
                    detail = data.get("error", f"HTTP {response.status}")
                    log.error(f"OpenRouter error from {url}: {detail}")
                    raise HTTPException(status_code=response.status, detail=detail)
                return data
    except Exception as e:
        log.exception(f"OpenRouter connection error: {e}")
        return None

@cached(ttl=3)
async def get_all_models(request: Request, user: UserModel) -> dict[str, list]:
    log.info("get_all_models() for OpenRouter")
    if not request.app.state.config.ENABLE_OPENROUTER_API:
        return {"data": []}
    responses = []
    for idx, url in enumerate(request.app.state.config.OPENROUTER_API_BASE_URLS):
        key = None
        if idx < len(request.app.state.config.OPENROUTER_API_KEYS):
            key = request.app.state.config.OPENROUTER_API_KEYS[idx]
        resp = await send_get_request(url, key=key, user=user)
        if resp and "data" in resp:
            responses.append(resp["data"])
    # merge lists
    merged = []
    for model_list in responses:
        merged.extend(
            {
                **model,
                "name": model.get("name", model.get("id")),
                "owned_by": "openrouter",
                "openrouter": model,
            }
            for model in model_list
        )
    models = {"data": merged}
    request.app.state.OPENROUTER_MODELS = {model["id"]: model for model in merged}
    return models

@router.get("/config")
async def get_config(request: Request, user=Depends(get_admin_user)):
    return {
        "ENABLE_OPENROUTER_API": request.app.state.config.ENABLE_OPENROUTER_API,
        "OPENROUTER_API_BASE_URLS": request.app.state.config.OPENROUTER_API_BASE_URLS,
        "OPENROUTER_API_KEYS": request.app.state.config.OPENROUTER_API_KEYS,
        "OPENROUTER_API_CONFIGS": request.app.state.config.OPENROUTER_API_CONFIGS,
    }

class OpenRouterConfigForm(BaseModel):
    ENABLE_OPENROUTER_API: Optional[bool] = None
    OPENROUTER_API_BASE_URLS: list[str]
    OPENROUTER_API_KEYS: list[str]
    OPENROUTER_API_CONFIGS: dict

@router.post("/config/update")
async def update_config(
    request: Request, form_data: OpenRouterConfigForm, user=Depends(get_admin_user)
):
    request.app.state.config.ENABLE_OPENROUTER_API = form_data.ENABLE_OPENROUTER_API
    request.app.state.config.OPENROUTER_API_BASE_URLS = form_data.OPENROUTER_API_BASE_URLS
    request.app.state.config.OPENROUTER_API_KEYS = form_data.OPENROUTER_API_KEYS
    # ensure equal length
    if len(request.app.state.config.OPENROUTER_API_KEYS) != len(
        request.app.state.config.OPENROUTER_API_BASE_URLS
    ):
        if len(request.app.state.config.OPENROUTER_API_KEYS) > len(
            request.app.state.config.OPENROUTER_API_BASE_URLS
        ):
            request.app.state.config.OPENROUTER_API_KEYS = (
                request.app.state.config.OPENROUTER_API_KEYS[: len(request.app.state.config.OPENROUTER_API_BASE_URLS)]
            )
        else:
            request.app.state.config.OPENROUTER_API_KEYS += [""] * (
                len(request.app.state.config.OPENROUTER_API_BASE_URLS)
                - len(request.app.state.config.OPENROUTER_API_KEYS)
            )
    request.app.state.config.OPENROUTER_API_CONFIGS = form_data.OPENROUTER_API_CONFIGS
    # prune configs
    keys = [str(i) for i in range(len(request.app.state.config.OPENROUTER_API_BASE_URLS))]
    request.app.state.config.OPENROUTER_API_CONFIGS = {
        k: v for k, v in request.app.state.config.OPENROUTER_API_CONFIGS.items() if k in keys
    }
    return {
        "ENABLE_OPENROUTER_API": request.app.state.config.ENABLE_OPENROUTER_API,
        "OPENROUTER_API_BASE_URLS": request.app.state.config.OPENROUTER_API_BASE_URLS,
        "OPENROUTER_API_KEYS": request.app.state.config.OPENROUTER_API_KEYS,
        "OPENROUTER_API_CONFIGS": request.app.state.config.OPENROUTER_API_CONFIGS,
    }

@router.get("/models")
@router.get("/models/{url_idx}")
async def get_models(
    request: Request, url_idx: Optional[int] = None, user=Depends(get_verified_user)
):
    if url_idx is None:
        models = await get_all_models(request, user)
    else:
        # single endpoint
        url = request.app.state.config.OPENROUTER_API_BASE_URLS[url_idx]
        key = None
        if url_idx < len(request.app.state.config.OPENROUTER_API_KEYS):
            key = request.app.state.config.OPENROUTER_API_KEYS[url_idx]
        resp = await send_get_request(url, key=key, user=user)
        data_list = resp.get("data", []) if resp else []
        models = {"data": data_list}
    # no local access control for OpenRouter
    return models 