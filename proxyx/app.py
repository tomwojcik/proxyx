import logging

import uvicorn
import yaml
from starlette import status
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from starlette.routing import Route

from proxyx import settings
from proxyx.errors import ProxyxError
from proxyx.models import Proxyx

proxyx_model = Proxyx.load(settings.PROXYX_ROUTING_CONFIG_PATH)


logger = logging.getLogger("proxyx")


async def handle_proxy_view(request: Request):
    if settings.LOG_ALL_HEADERS:
        logger.info(
            f"Headers for {request.method} {request.url}: {request.headers}"
        )
    for router in proxyx_model.routers:
        for matching_rule in router.matching_rules:
            if matching_rule.is_matching(request):
                return await router.route(request)
    raise ProxyxError(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"'{request.url}' is not matching any route patterns",
    )


routes = [
    Route("/{path:path}", handle_proxy_view),
]

middleware = [
    Middleware(GZipMiddleware),
    Middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOW_ORIGINS,
        allow_methods=settings.ALLOW_METHODS,
        allow_headers=settings.ALLOW_HEADERS,
        allow_credentials=settings.ALLOW_CREDENTIALS,
        allow_origin_regex=settings.ALLOW_ORIGIN_REGEX,
    ),
    Middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS),
]

app = Starlette(debug=settings.DEBUG, routes=routes, middleware=middleware)


@app.on_event("startup")
async def startup_event():
    config_path = (settings.ROOT_DIR / "proxyx" / "logging.yaml").as_posix()
    with open(config_path, "rb") as fd:
        config = yaml.load(fd, Loader=yaml.SafeLoader)
    logging.config.dictConfig(config)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, proxy_headers=True)
