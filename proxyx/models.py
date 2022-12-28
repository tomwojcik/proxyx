import contextlib
import logging
import re
import typing

import httpx
from httpx import URL as httpx_url
from pydantic import Extra
from pydantic import Field
from pydantic import validator
from pydantic_yaml import YamlModel
from starlette import status
from starlette.background import BackgroundTask
from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import Response
from starlette.responses import StreamingResponse

from proxyx import settings
from proxyx import utils
from proxyx.errors import ProxyxError

with contextlib.suppress(ImportError):
    import sentry_sdk
    from sentry_sdk.integrations.httpx import HttpxIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[HttpxIntegration(), StarletteIntegration()],
    )

logger = logging.getLogger("proxyx")

client = httpx.AsyncClient(follow_redirects=True)


class BaseModel(YamlModel, extra=Extra.forbid):
    pass


class MatchingRule(BaseModel):
    url_patterns: typing.List[typing.Union[str, typing.Pattern]] = Field(
        default=["*"],
        title="URL Patterns",
        description=(
            "A list of regex patterns for matching request urls. "
            "If one of the patterns is matching, this router will be used. "
            "The only non-regex special value allowed is an asterix (``*``). "
            "If used, it will catch all incoming requests. "
            "Used by default, if no other value is provided. "
            "If multiple routers match the same request url, "
            "only the first one will be used."
        ),
    )
    header_patterns: typing.Dict[str, typing.Any] = Field(
        default={},
        title="Header Patterns",
        description=(
            "If you need to route based on header value, "
            "put your matching rule here. "
            "It accepts regex and an asterix (``*``) for catch-all."
        ),
    )

    @validator("header_patterns")
    def initialize_header_patterns(
        cls, patterns: typing.Dict[str, str]
    ) -> typing.Dict[str, typing.Union[str, typing.Pattern]]:
        """
        Initializes header_patterns, from string to compiled Python regex
        pattern.

        :param patterns: Dict of header name: header pattern as string.
        :return: Dict of header name: header pattern as a compiled pattern.
        """
        return dict(
            zip(
                patterns.keys(),
                utils.load_string_patterns(list(patterns.values())),
            )
        )

    @validator("url_patterns")
    def initialize_url_patterns(
        cls, patterns: typing.List[str]
    ) -> typing.List[typing.Union[str, typing.Pattern]]:
        """
        Initializes url_patterns, from string to compiled Python regex
        pattern.

        :param patterns: List of patterns as strings.
        :return: List of initialized patterns, compiled once.
        """
        return utils.load_string_patterns(patterns)

    def _are_headers_matching(self, request: Request) -> bool:
        if not self.header_patterns:
            return True
        for header_key, compiled_header_pattern in self.header_patterns:
            if header_key not in request.headers:
                return False

            compiled_header_pattern: re.Pattern
            given_header_value = request.headers[header_key]
            if not compiled_header_pattern.match(given_header_value):
                return False

        return True

    def _are_url_patterns_matching(self, request: Request) -> bool:
        if "*" in self.url_patterns:
            return True

        for pattern in self.url_patterns:
            pattern: re.Pattern
            if pattern.match(str(request.url)):
                return True
        return False

    def is_matching(self, request: Request) -> bool:
        """
        Allows to determine whether the request url matches one of the router
        url patterns.

        :param request: ASGI request
        """
        return self._are_headers_matching(
            request
        ) and self._are_url_patterns_matching(request)


class Router(BaseModel):
    """
    A custom object that defines three steps:

    - matching criteria for incoming request,
    - how to validate the request,
    - where to pass it.
    """

    matching_rules: typing.List[MatchingRule]
    replace_target_host: str = Field(
        default=None,
        title="Target host",
        description="Will replace the incoming request host with this one.",
    )
    force_https: bool = Field(
        default=True,
        description=(
            "Whether to always use https, even if http is provided from the"
            " downstream."
        ),
    )
    request_path_has_full_path: bool = Field(
        default=True,
        title="Request path has full path",
        description=(
            "Request expects one optional attribute. "
            "It might be the entire path www.example.com/resource, "
            "or just /resource."
        ),
    )

    required_headers: typing.Dict[str, typing.Pattern] = Field(
        default={},
        title="Required Headers",
        description=(
            "For each key-value pair, where key is the header key and value is"
            " a regex pattern,validate whether the key exists. If so, validate"
            " if the value is matching the regex pattern.An asterix (``*``) is"
            " a special value that will allow for any value."
        ),
    )

    async def route(self, request):
        """
        Validates and forwards the request.

        :param request: ASGI Request
        :return: Upstream response.
        """
        logger.info(f"Processing {request}")
        self._validate_request(request)
        return await self._forward_request(request)

    def _validate_request(self, request: Request):
        """
        A single validation place where all validation is happening. If
        passed, the request is forwarded.

        :param request: ASGI Request
        """
        for required_header in self.required_headers.keys():
            if required_header not in request.headers:
                raise ProxyxError(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One of the required headers is missing",
                )

        for (
            required_header_key,
            header_pattern,
        ) in self.required_headers.items():
            if header_pattern == "*":
                continue
            header_value = request.headers[required_header_key]
            if not header_pattern.match(header_value):
                raise ProxyxError(
                    status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Incorrect header value for header"
                        f" '{required_header_key}'"
                    ),
                )

    @validator("required_headers")
    def initialize_required_headers(
        cls, d
    ) -> typing.Dict[str, typing.Union[str, typing.Pattern]]:
        """
        Changes expected key value pairs into key value where value is a
        loaded regex pattern.

        :param patterns: List of patterns as strings.
        :return: List of initialized patterns, compiled once.
        """
        parsed_values = utils.load_string_patterns(d.values())
        return dict(zip(d.keys(), parsed_values))

    def _prepare_url(self, request: Request) -> URL:
        if self.request_path_has_full_path:
            path = request.path_params.get("path")
            if not path.startswith("http"):
                path = f"https://{path}"
            url = URL(path)
        else:
            url = request.url

        if self.replace_target_host:
            replace_target_host = self.replace_target_host
            if not replace_target_host.startswith("http"):
                replace_target_host = f"https://{replace_target_host}"
            target_parse_result = URL(replace_target_host)
            if target_parse_result.scheme:
                url = url.replace(scheme=target_parse_result.scheme)
            if target_parse_result.port:
                url = url.replace(port=target_parse_result.port)

            url = url.replace(netloc=target_parse_result.netloc)

        if self.force_https:
            url = url.replace(scheme="https")

        if not url.scheme:
            url = url.replace(scheme="http")

        if not url.netloc:
            raise ProxyxError(detail=f"Invalid url, missing netloc in {url}")
        return url

    async def _forward_request(self, request: Request) -> Response:
        """
        Asynchronously executes upstream fetch.

        :param request: ASGI request
        :return: Response from the upstream.
        """
        url = self._prepare_url(request)

        if url.netloc == "favicon.ico":
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        filtered_headers = {
            k: v for k, v in request.headers.items() if k not in ("host",)
        }

        kwargs = dict(
            method=request.method,
            url=httpx_url(str(url)),
            headers=filtered_headers,
        )
        if request.method in ("PUT", "PATCH", "POST"):
            kwargs["content"] = request.stream()

        upstream_request = client.build_request(**kwargs)

        upstream_response = await client.send(
            upstream_request, stream=True, follow_redirects=True
        )
        # docs https://www.python-httpx.org/async/#streaming-responses
        return StreamingResponse(
            upstream_response.aiter_raw(),
            status_code=upstream_response.status_code,
            headers=upstream_response.headers,
            background=BackgroundTask(upstream_response.aclose),
        )


class Proxyx(BaseModel):
    """
    Main object that holds all the information about all the routers.

    It is used directly in the view.
    """

    routers: typing.List[Router] = Field(
        title="Routers", description="A list of router objects."
    )

    @classmethod
    def load(cls, file_path: str) -> "Proxyx":
        """
        Loads the proxy configuration from the yaml file.

        The path to this file needs to be specified as env variable
        ROUTING_CONFIG_PATH.
        """
        return cls.parse_file(file_path)
