from collections.abc import Callable
from typing import Any

from fastapi import APIRouter as FastAPIRouter
from fastapi.types import DecoratedCallable


class APIRouter(FastAPIRouter):
    """
    A custom API router that extends FastAPI's APIRouter to handle trailing slashes
    in endpoint paths more gracefully.

    This router ensures that both versions of a path (with and without a trailing slash)
    are registered. The version without the trailing slash is included in the OpenAPI schema,
    while the version with the trailing slash is excluded.

    This behavior is mandatory for reverse proxies behind Kubernetes, as Kubernetes ingress
    controllers often normalize paths by removing or adding trailing slashes, which can lead
    to unexpected 404 errors if both versions of the path are not handled.

    Additionally, this router ensures that URLs are properly constructed with the correct
    scheme (http or https) to avoid issues such as "location: http" when the browser expects
    "location: https". This is particularly important when running behind a reverse proxy
    that terminates SSL.

    Methods:
        api_route(path: str, *, include_in_schema: bool = True, **kwargs: Any) -> Callable:
            Overrides the `api_route` method to register both the primary path and an
            alternate path with a trailing slash. The alternate path is excluded from
            the OpenAPI schema.
    """

    def api_route(
        self, path: str, *, include_in_schema: bool = True, **kwargs: Any
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        if path.endswith("/"):
            path = path[:-1]

        add_path = super().api_route(path, include_in_schema=include_in_schema, **kwargs)

        alternate_path = path + "/"
        add_alternate_path = super().api_route(alternate_path, include_in_schema=False, **kwargs)

        def decorator(func: DecoratedCallable) -> DecoratedCallable:
            add_alternate_path(func)
            return add_path(func)

        return decorator
