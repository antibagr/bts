import functools
import typing

import aiocache
import aiocache.plugins  # type: ignore[import-untyped]
import aiocache.serializers  # type: ignore[import-untyped]

from app.settings import settings

if typing.TYPE_CHECKING:
    from app.dto.annotations import F, P, T

    def _skip_cache_func(val: typing.Any, /) -> typing.Literal[False]:  # noqa: ARG001, ANN401
        """Never skip caching."""
        return False

    # NOTE (rudiemeant@gmail.com): I've had to add the type hints to the `cached` function
    # because the `aiocache.cached` function is not typed correctly.
    def cached(  # noqa: PLR0913, D417
        *,
        ttl: int | None = aiocache.base.SENTINEL,
        key: str | None = None,
        namespace: str | None = None,
        key_builder: typing.Callable[..., str] | None = None,
        skip_cache_func: typing.Callable[..., bool] = _skip_cache_func,
        cache: type[aiocache.base.BaseCache] = aiocache.Cache.MEMORY,
        serializer: aiocache.serializers.BaseSerializer | None = None,
        plugins: list[aiocache.plugins.BasePlugin] | None = None,
        alias: str | None = None,
        noself: bool = False,
        cache_read: bool = True,
        cache_write: bool = True,
        aiocache_wait_for_write: bool = True,
    ) -> typing.Callable[[F[P, T]], F[P, T]]:
        """Cache the function's return value into a key generated with module_name,
        function_name, and args. The cache is accessible via `<function_name>.cache`.

        In some scenarios, additional arguments are necessary for cache configuration,
        such as endpoint and port for Redis cache.
        These can be supplied as kwargs and will be propagated accordingly.

        A single cache instance is created per decorated call.
        High concurrency on the same function may require pool size adjustments.

        Args:
        ----
            ttl (int):
                Time in seconds to store the function call. Defaults to None, indicating no expiration.
            key (str):
                Key for the function return. Takes precedence over `key_builder`.
                Defaults to a combination of module_name, function_name, args, and kwargs
                if neither key nor key_builder are provided.
            namespace (str):
                Prefix for the key used in all backend operations. Defaults to None.
            key_builder (Callable):
                Allows dynamic key construction. Receives the function and the same args and kwargs.
            skip_cache_func (Callable):
                Determines whether to skip caching the result.
                For example, to avoid caching None results, use `lambda r: r is None`.
            cache (cache class):
                Cache class for `set`/`get` operations. Defaults to `aiocache.SimpleMemoryCache`.
            serializer:
                Serializer instance for `dumps`/`loads`. Defaults to the cache backend's default serializer.
            plugins (list):
                Plugins for cmd hooks. Defaults to those from the cache class.
            alias (str):
                Config alias. Other config parameters are ignored if alias is provided.
                Use explicit parameters for a per function cache.
            noself (bool):
                If decorating a class function, set to True to exclude `self` from the key generation.
                Defaults to False.
            cache_read (bool):
                Tries to read from cache before executing the function. Enabled by default.
            cache_write (bool):
                Writes the result to the cache after retrieval. Enabled by default.
            aiocache_wait_for_write (bool):
                Waits for the write to complete before returning.
                Enabled by default, set to False for background write.

        Only one cache instance is created per decorated call.
        Adapt pool size for high concurrency.

        Note:
        ----
            Use `noself=True` to exclude `self` from key generation in class methods,
            preventing different instances from creating unique keys for the same function calls.

        """

        def _cached(func: F[P, T]) -> F[P, T]:
            @functools.wraps(func)
            async def _wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                result = await aiocache.cached(
                    ttl=ttl,
                    key=key,
                    namespace=namespace,
                    key_builder=key_builder,
                    skip_cache_func=skip_cache_func,
                    cache=cache,
                    serializer=serializer,
                    plugins=plugins,
                    alias=alias,
                    noself=noself,
                )(func)(
                    *args,
                    cache_read=cache_read,
                    cache_write=cache_write,
                    aiocache_wait_for_write=aiocache_wait_for_write,
                    **kwargs,
                )
                return typing.cast(T, result)

            return _wrapper

        return _cached

    cached = functools.partial(cached, noself=True, ttl=60, cache=settings.CACHE_TYPE, aiocache_wait_for_write=False)
else:
    cached = functools.partial(aiocache.cached, noself=True, ttl=60, cache=settings.CACHE_TYPE)
