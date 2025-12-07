import asyncio
import grpc
from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
import logging
from contextlib import asynccontextmanager

from .exceptions import ConnectionError, TimeoutError
from .utils import ExponentialBackoff, AsyncRateLimiter, retry_async

logger = logging.getLogger(__name__)


class AsyncBaseClient(ABC):
    """
    Базовый абстрактный класс для асинхронных gRPC клиентов.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 50051,
        max_retries: int = 3,
        timeout: float = 30.0,
        rate_limit: Optional[float] = None,
        enable_logging: bool = True,
    ):
        """
        Инициализация базового клиента.

        Args:
            host: Хост сервера
            port: Порт сервера
            max_retries: Максимальное количество повторных попыток
            timeout: Таймаут операций в секундах
            rate_limit: Ограничение запросов в секунду
            enable_logging: Включить логирование
        """
        self.host = host
        self.port = port
        self.max_retries = max_retries
        self.timeout = timeout
        self.channel = None
        self.backoff = ExponentialBackoff(max_retries=max_retries)
        self.rate_limiter = AsyncRateLimiter(rate_limit, 1.0) if rate_limit else None

        if enable_logging:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )

    @abstractmethod
    async def connect(self):
        """Подключиться к серверу."""
        pass

    @abstractmethod
    async def close(self):
        """Закрыть соединение."""
        pass

    @abstractmethod
    async def ping(self) -> bool:
        """Проверить доступность сервера."""
        pass

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _rate_limit(self):
        """Применить ограничение скорости."""
        if self.rate_limiter:
            await self.rate_limiter.wait()

    async def _with_retry(self, func, *args, **kwargs):
        """Выполнить функцию с повторными попытками."""
        return await retry_async(
            func,
            *args,
            max_retries=self.max_retries,
            base_delay=1.0,
            retry_exceptions=(grpc.RpcError, ConnectionError, TimeoutError),
            **kwargs,
        )

    async def _create_channel(self, options: Optional[list] = None) -> grpc.aio.Channel:
        """
        Создать асинхронный канал.

        Args:
            options: Дополнительные опции канала

        Returns:
            grpc.aio.Channel: Асинхронный канал
        """
        default_options = [
            ("grpc.keepalive_time_ms", 10000),
            ("grpc.keepalive_timeout_ms", 5000),
            ("grpc.keepalive_permit_without_calls", True),
            ("grpc.max_reconnect_backoff_ms", 10000),
        ]

        if options:
            default_options.extend(options)

        return grpc.aio.insecure_channel(
            f"{self.host}:{self.port}", options=default_options
        )

    @asynccontextmanager
    async def _timeout_context(self, custom_timeout: Optional[float] = None):
        """
        Контекстный менеджер для таймаута.

        Args:
            custom_timeout: Кастомный таймаут (по умолчанию используется self.timeout)
        """
        timeout = custom_timeout or self.timeout

        try:
            await asyncio.wait_for(asyncio.sleep(0), timeout=timeout)
            yield
        except asyncio.TimeoutError:
            raise TimeoutError(f"Operation timed out after {timeout}s")

    def _handle_grpc_error(self, e: grpc.RpcError, operation: str) -> None:
        """
        Обработать gRPC ошибку.

        Args:
            e: Исключение gRPC
            operation: Название операции
        """
        from .exceptions import (
            NotFoundError,
            AuthenticationError,
            ResourceExhaustedError,
            ValidationError,
        )

        error_map = {
            grpc.StatusCode.NOT_FOUND: NotFoundError,
            grpc.StatusCode.UNAUTHENTICATED: AuthenticationError,
            grpc.StatusCode.PERMISSION_DENIED: AuthenticationError,
            grpc.StatusCode.RESOURCE_EXHAUSTED: ResourceExhaustedError,
            grpc.StatusCode.INVALID_ARGUMENT: ValidationError,
            grpc.StatusCode.FAILED_PRECONDITION: ValidationError,
        }

        exception_class = error_map.get(e.code())
        if exception_class:
            raise exception_class(f"{operation} failed: {e.details()}")

        from .exceptions import SimulationError

        raise SimulationError(f"{operation} failed: {e.details()}")
