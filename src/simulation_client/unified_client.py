import asyncio
from typing import Optional, List, Dict, Any
import logging

from .simulation_client import AsyncSimulationClient
from .database_client import AsyncDatabaseClient
from .models import *
from .exceptions import *

logger = logging.getLogger(__name__)


class AsyncUnifiedClient:
    """
    Объединенный клиент для работы с обоими сервисами.

    Фасад, который скрывает сложность работы с двумя разными сервисами.

    Пример использования:
    ```python
    async with AsyncUnifiedClient(
        sim_host="localhost",
        sim_port=50051,
        db_host="localhost",
        db_port=50052
    ) as client:
        # Получаем ресурсы из базы
        suppliers = await client.get_all_suppliers()
        logists = await client.get_all_logists()

        # Создаем и настраиваем симуляцию
        simulation = await client.create_simulation()
        await client.configure_simulation(
            simulation_id=simulation.simulation_id,
            logist_id=logists[0].worker_id,
            supplier_ids=[s.supplier_id for s in suppliers[:2]]
        )

        # Запускаем симуляцию
        results = await client.run_simulation(simulation.simulation_id)
    ```
    """

    def __init__(
        self,
        sim_host: str = "localhost",
        sim_port: int = 50051,
        db_host: str = "localhost",
        db_port: int = 50052,
        max_retries: int = 3,
        timeout: float = 30.0,
        rate_limit: Optional[float] = None,
        enable_logging: bool = True,
    ):
        """
        Инициализация объединенного клиента.

        Args:
            sim_host: Хост сервиса симуляции
            sim_port: Порт сервиса симуляции
            db_host: Хост сервиса базы данных
            db_port: Порт сервиса базы данных
            max_retries: Максимальное количество повторных попыток
            timeout: Таймаут операций
            rate_limit: Ограничение запросов
            enable_logging: Включить логирование
        """
        self.sim_client = AsyncSimulationClient(
            host=sim_host,
            port=sim_port,
            max_retries=max_retries,
            timeout=timeout,
            rate_limit=rate_limit,
            enable_logging=enable_logging,
        )

        self.db_client = AsyncDatabaseClient(
            host=db_host,
            port=db_port,
            max_retries=max_retries,
            timeout=timeout,
            rate_limit=rate_limit,
            enable_logging=enable_logging,
        )

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def connect(self):
        """Подключиться к обоим сервисам."""
        logger.info("Connecting to services...")

        # Подключаемся параллельно к обоим сервисам
        await asyncio.gather(self.sim_client.connect(), self.db_client.connect())

        logger.info("Connected to all services")

    async def close(self):
        """Закрыть соединения с обоими сервисами."""
        logger.info("Closing connections...")

        await asyncio.gather(
            self.sim_client.close(),
            self.db_client.close(),
            return_exceptions=True,  # Закрываем оба, даже если один упал
        )

        logger.info("All connections closed")

    async def ping(self) -> Dict[str, bool]:
        """
        Проверить доступность всех сервисов.

        Returns:
            Dict: Статус каждого сервиса
        """
        results = await asyncio.gather(
            self.sim_client.ping(), self.db_client.ping(), return_exceptions=True
        )

        return {
            "simulation_service": isinstance(results[0], bool) and results[0],
            "database_service": isinstance(results[1], bool) and results[1],
        }

    # ==================== Прокси-методы для SimulationService ====================

    async def create_simulation(self) -> SimulationConfig:
        """Создать новую симуляцию."""
        return await self.sim_client.create_simulation()

    async def get_simulation(self, simulation_id: str) -> Dict[str, Any]:
        """Получить информацию о симуляции."""
        return await self.sim_client.get_simulation(simulation_id)

    async def run_simulation(self, simulation_id: str) -> SimulationResults:
        """Запустить симуляцию."""
        return await self.sim_client.run_simulation(simulation_id)

    async def set_logist(self, simulation_id: str, worker_id: str) -> bool:
        """Назначить логиста."""
        return await self.sim_client.set_logist(simulation_id, worker_id)

    # ==================== Прокси-методы для DatabaseManager ====================

    async def get_all_suppliers(self) -> List[SupplierModel]:
        """Получить всех поставщиков."""
        return await self.db_client.get_all_suppliers()

    async def get_all_workers(self) -> List[WorkerModel]:
        """Получить всех работников."""
        return await self.db_client.get_all_workers()

    async def get_all_logists(self) -> List[LogistModel]:
        """Получить всех логистов."""
        return await self.db_client.get_all_logists()

    async def get_all_equipment(self) -> List[EquipmentModel]:
        """Получить всё оборудование."""
        return await self.db_client.get_all_equipment()

    async def get_all_tenders(self) -> List[TenderModel]:
        """Получить все тендеры."""
        return await self.db_client.get_all_tenders()

    # ==================== Комбинированные методы ====================

    async def configure_simulation(
        self,
        simulation_id: str,
        logist_id: Optional[str] = None,
        supplier_ids: Optional[List[str]] = None,
        backup_supplier_ids: Optional[List[str]] = None,
        equipment_assignments: Optional[Dict[str, str]] = None,
        tender_ids: Optional[List[str]] = None,
    ) -> bool:
        """
        Комплексная настройка симуляции.

        Args:
            simulation_id: ID симуляции
            logist_id: ID логиста
            supplier_ids: Список ID основных поставщиков
            backup_supplier_ids: Список ID запасных поставщиков
            equipment_assignments: {workplace_id: equipment_id}
            tender_ids: Список ID тендеров

        Returns:
            bool: True если все настройки применены успешно
        """
        tasks = []

        # Настройка логиста
        if logist_id:
            tasks.append(self.sim_client.set_logist(simulation_id, logist_id))

        # Настройка поставщиков
        if supplier_ids:
            for supplier_id in supplier_ids:
                tasks.append(
                    self.sim_client.add_supplier(simulation_id, supplier_id, False)
                )

        if backup_supplier_ids:
            for supplier_id in backup_supplier_ids:
                tasks.append(
                    self.sim_client.add_supplier(simulation_id, supplier_id, True)
                )

        # Настройка оборудования
        if equipment_assignments:
            for workplace_id, equipment_id in equipment_assignments.items():
                tasks.append(
                    self.sim_client.set_equipment_on_workplace(
                        simulation_id, workplace_id, equipment_id
                    )
                )

        # Настройка тендеров
        if tender_ids:
            for tender_id in tender_ids:
                tasks.append(self.sim_client.add_tender(simulation_id, tender_id))

        # Выполняем все задачи параллельно
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Проверяем результаты
            success_count = sum(1 for r in results if not isinstance(r, Exception))
            error_count = len(results) - success_count

            if error_count > 0:
                logger.warning(
                    f"Configured {success_count} out of {len(results)} settings"
                )

            return error_count == 0

        return True

    async def run_complete_scenario(
        self, config: Optional[Dict[str, Any]] = None
    ) -> SimulationResults:
        """
        Запустить полный сценарий: создание, настройка и запуск симуляции.

        Args:
            config: Конфигурация симуляции

        Returns:
            SimulationResults: Результаты симуляции
        """
        config = config or {}

        # 1. Создаем симуляцию
        simulation = await self.create_simulation()

        # 2. Настраиваем симуляцию
        await self.configure_simulation(
            simulation_id=simulation.simulation_id,
            logist_id=config.get("logist_id"),
            supplier_ids=config.get("supplier_ids"),
            backup_supplier_ids=config.get("backup_supplier_ids"),
            equipment_assignments=config.get("equipment_assignments"),
            tender_ids=config.get("tender_ids"),
        )

        # 3. Запускаем симуляцию
        return await self.run_simulation(simulation.simulation_id)

    async def get_available_resources(self) -> Dict[str, List]:
        """
        Получить все доступные ресурсы параллельно.

        Returns:
            Dict: Все ресурсы
        """
        tasks = {
            "suppliers": self.get_all_suppliers(),
            "workers": self.get_all_workers(),
            "logists": self.get_all_logists(),
            "equipment": self.get_all_equipment(),
            "tenders": self.get_all_tenders(),
        }

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        return {
            key: result if not isinstance(result, Exception) else []
            for key, result in zip(tasks.keys(), results)
        }
