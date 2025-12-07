import asyncio
import grpc
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from .base_client import AsyncBaseClient
from .proto import simulator_pb2
from .proto import simulator_pb2_grpc
from .models import *
from .exceptions import *
from .utils import proto_to_dict

logger = logging.getLogger(__name__)


class AsyncSimulationClient(AsyncBaseClient):
    """
    Асинхронный клиент для SimulationService.

    Работает на порту 50051 (или другом указанном порту).

    Пример использования:
    ```python
    async with AsyncSimulationClient("localhost", 50051) as client:
        simulation = await client.create_simulation()
        await client.set_logist(simulation.simulation_id, "logist_123")
        results = await client.run_simulation(simulation.simulation_id)
    ```
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 50051,  # 👈 Порт для SimulationService
        max_retries: int = 3,
        timeout: float = 30.0,
        rate_limit: Optional[float] = None,
        enable_logging: bool = True,
    ):
        super().__init__(host, port, max_retries, timeout, rate_limit, enable_logging)
        self.stub = None

    async def connect(self):
        """Подключиться к серверу SimulationService."""
        try:
            self.channel = await self._create_channel()
            self.stub = simulator_pb2_grpc.SimulationServiceStub(self.channel)

            # Проверяем соединение
            if await self.ping():
                logger.info(
                    f"Connected to SimulationService at {self.host}:{self.port}"
                )
            else:
                raise ConnectionError(
                    f"Cannot connect to SimulationService at {self.host}:{self.port}"
                )

        except Exception as e:
            logger.error(f"Failed to connect to SimulationService: {e}")
            raise ConnectionError(f"Connection to SimulationService failed: {e}")

    async def close(self):
        """Закрыть соединение."""
        if self.channel:
            await self.channel.close()
            logger.info("Disconnected from SimulationService")

    async def ping(self) -> bool:
        """
        Проверить доступность SimulationService.

        Returns:
            bool: True если сервер доступен
        """
        try:
            async with self._timeout_context(5.0):  # Короткий таймаут для ping
                await self._rate_limit()
                response = await self.stub.ping(simulator_pb2.PingRequest())
                return response.success
        except Exception as e:
            logger.warning(f"Ping to SimulationService failed: {e}")
            return False

    # ==================== Основные операции симуляции ====================

    async def create_simulation(self) -> SimulationConfig:
        """
        Создать новую симуляцию.

        Returns:
            SimulationConfig: Конфигурация созданной симуляции
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                response = await self._with_retry(
                    self.stub.create_simulation, simulator_pb2.CreateSimulationRquest()
                )

                sim = response.simulation
                return SimulationConfig(
                    simulation_id=sim.simulation_id, capital=sim.capital
                )

        except grpc.RpcError as e:
            self._handle_grpc_error(e, "Create simulation")

    async def get_simulation(self, simulation_id: str) -> Dict[str, Any]:
        """
        Получить информацию о симуляции.

        Args:
            simulation_id: ID симуляции

        Returns:
            Dict: Информация о симуляции
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                response = await self._with_retry(
                    self.stub.get_simulation,
                    simulator_pb2.GetSimulationRequest(simulation_id=simulation_id),
                )
                return proto_to_dict(response.simulation)

        except grpc.RpcError as e:
            self._handle_grpc_error(e, "Get simulation")

    async def run_simulation(self, simulation_id: str) -> SimulationResults:
        """
        Запустить симуляцию.

        Args:
            simulation_id: ID симуляции

        Returns:
            SimulationResults: Результаты симуляции
        """
        try:
            async with self._timeout_context(
                self.timeout * 3
            ):  # Дольше для запуска симуляции
                await self._rate_limit()
                response = await self._with_retry(
                    self.stub.run_simulation,
                    simulator_pb2.RunSimulationRequest(simulation_id=simulation_id),
                )

                sim = response.simulation
                return SimulationResults(
                    profit=sim.results.profit,
                    cost=sim.results.cost,
                    profitability=sim.results.profitability,
                    capital=sim.capital,
                    step=sim.step,
                    timestamp=datetime.fromisoformat(
                        response.timestamp.replace("Z", "+00:00")
                    ),
                )

        except grpc.RpcError as e:
            self._handle_grpc_error(e, "Run simulation")

    # ==================== Управление логистами ====================

    async def set_logist(self, simulation_id: str, worker_id: str) -> bool:
        """
        Назначить логиста для симуляции.

        Args:
            simulation_id: ID симуляции
            worker_id: ID работника-логиста

        Returns:
            bool: True если успешно
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                await self._with_retry(
                    self.stub.set_logist,
                    simulator_pb2.SetLogistRequest(
                        simulation_id=simulation_id, worker_id=worker_id
                    ),
                )
                logger.info(f"Set logist {worker_id} for simulation {simulation_id}")
                return True

        except grpc.RpcError as e:
            logger.error(f"Failed to set logist {worker_id}: {e}")
            return False

    # ==================== Управление поставщиками ====================

    async def add_supplier(
        self, simulation_id: str, supplier_id: str, is_backup: bool = False
    ) -> bool:
        """
        Добавить поставщика в симуляцию.

        Args:
            simulation_id: ID симуляции
            supplier_id: ID поставщика
            is_backup: Является ли запасным поставщиком

        Returns:
            bool: True если успешно
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                await self._with_retry(
                    self.stub.add_supplier,
                    simulator_pb2.AddSupplierRequest(
                        simulation_id=simulation_id,
                        supplier_id=supplier_id,
                        is_backup=is_backup,
                    ),
                )
                logger.info(
                    f"Added supplier {supplier_id} to simulation {simulation_id}"
                )
                return True

        except grpc.RpcError as e:
            logger.error(f"Failed to add supplier {supplier_id}: {e}")
            return False

    async def delete_supplier(self, simulation_id: str, supplier_id: str) -> bool:
        """
        Удалить поставщика из симуляции.

        Args:
            simulation_id: ID симуляции
            supplier_id: ID поставщика

        Returns:
            bool: True если успешно
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                await self._with_retry(
                    self.stub.delete_supplier,
                    simulator_pb2.DeleteSupplierRequest(
                        simulation_id=simulation_id, supplier_id=supplier_id
                    ),
                )
                logger.info(
                    f"Deleted supplier {supplier_id} from simulation {simulation_id}"
                )
                return True

        except grpc.RpcError as e:
            logger.error(f"Failed to delete supplier {supplier_id}: {e}")
            return False

    # ==================== Управление складом ====================

    async def set_warehouse_worker(
        self, simulation_id: str, worker_id: str, warehouse_type: WarehouseType
    ) -> bool:
        """
        Назначить работника на склад.

        Args:
            simulation_id: ID симуляции
            worker_id: ID работника
            warehouse_type: Тип склада

        Returns:
            bool: True если успешно
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                await self._with_retry(
                    self.stub.set_warehouse_inventory_worker,
                    simulator_pb2.SetWarehouseInventoryWorkerRequest(
                        simulation_id=simulation_id,
                        worker_id=worker_id,
                        warehouse_type=warehouse_type.value,
                    ),
                )
                logger.info(
                    f"Set worker {worker_id} on {warehouse_type.value} warehouse"
                )
                return True

        except grpc.RpcError as e:
            logger.error(f"Failed to set warehouse worker {worker_id}: {e}")
            return False

    async def increase_warehouse_size(
        self, simulation_id: str, warehouse_type: WarehouseType, size: int
    ) -> bool:
        """
        Увеличить размер склада.

        Args:
            simulation_id: ID симуляции
            warehouse_type: Тип склада
            size: На сколько увеличить

        Returns:
            bool: True если успешно
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                await self._with_retry(
                    self.stub.increase_warehouse_size,
                    simulator_pb2.IncreaseWarehouseSizeRequest(
                        simulation_id=simulation_id,
                        warehouse_type=warehouse_type.value,
                        size=size,
                    ),
                )
                logger.info(
                    f"Increased {warehouse_type.value} warehouse size by {size}"
                )
                return True

        except grpc.RpcError as e:
            logger.error(f"Failed to increase warehouse size: {e}")
            return False

    # ==================== Управление рабочими местами ====================

    async def set_worker_on_workplace(
        self, simulation_id: str, worker_id: str, workplace_id: str
    ) -> bool:
        """
        Назначить работника на рабочее место.

        Args:
            simulation_id: ID симуляции
            worker_id: ID работника
            workplace_id: ID рабочего места

        Returns:
            bool: True если успешно
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                await self._with_retry(
                    self.stub.set_worker_on_workerplace,
                    simulator_pb2.SetWorkerOnWorkerplaceRequest(
                        simulation_id=simulation_id,
                        worker_id=worker_id,
                        workplace_id=workplace_id,
                    ),
                )
                logger.info(f"Set worker {worker_id} on workplace {workplace_id}")
                return True

        except grpc.RpcError as e:
            logger.error(f"Failed to set worker on workplace: {e}")
            return False

    async def set_equipment_on_workplace(
        self, simulation_id: str, workplace_id: str, equipment_id: str
    ) -> bool:
        """
        Установить оборудование на рабочее место.

        Args:
            simulation_id: ID симуляции
            workplace_id: ID рабочего места
            equipment_id: ID оборудования

        Returns:
            bool: True если успешно
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                await self._with_retry(
                    self.stub.set_equipment_on_workplace,
                    simulator_pb2.SetEquipmentOnWorkplaceRequst(
                        simulation_id=simulation_id,
                        workplace_id=workplace_id,
                        equipment_id=equipment_id,
                    ),
                )
                logger.info(f"Set equipment {equipment_id} on workplace {workplace_id}")
                return True

        except grpc.RpcError as e:
            logger.error(f"Failed to set equipment on workplace: {e}")
            return False

    # ==================== Управление тендерами ====================

    async def add_tender(self, simulation_id: str, tender_id: str) -> bool:
        """
        Добавить тендер в симуляцию.

        Args:
            simulation_id: ID симуляции
            tender_id: ID тендера

        Returns:
            bool: True если успешно
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                await self._with_retry(
                    self.stub.add_tender,
                    simulator_pb2.AddTenderRequest(
                        simulation_id=simulation_id, tender_id=tender_id
                    ),
                )
                logger.info(f"Added tender {tender_id} to simulation {simulation_id}")
                return True

        except grpc.RpcError as e:
            logger.error(f"Failed to add tender {tender_id}: {e}")
            return False

    async def delete_tender(self, simulation_id: str, tender_id: str) -> bool:
        """
        Удалить тендер из симуляции.

        Args:
            simulation_id: ID симуляции
            tender_id: ID тендера

        Returns:
            bool: True если успешно
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                await self._with_retry(
                    self.stub.delete_tender,
                    simulator_pb2.RemoveTenderRequest(
                        simulation_id=simulation_id, tender_id=tender_id
                    ),
                )
                logger.info(
                    f"Deleted tender {tender_id} from simulation {simulation_id}"
                )
                return True

        except grpc.RpcError as e:
            logger.error(f"Failed to delete tender {tender_id}: {e}")
            return False

    # ==================== Дополнительные настройки ====================

    async def set_dealing_with_defects(self, simulation_id: str, policy: str) -> bool:
        """
        Установить политику работы с браком.

        Args:
            simulation_id: ID симуляции
            policy: Политика работы с браком

        Returns:
            bool: True если успешно
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                await self._with_retry(
                    self.stub.set_dealing_with_defects,
                    simulator_pb2.SetDealingWithDefectsRequest(
                        simulation_id=simulation_id, dealing_with_defects=policy
                    ),
                )
                logger.info(
                    f"Set defects policy to {policy} for simulation {simulation_id}"
                )
                return True

        except grpc.RpcError as e:
            logger.error(f"Failed to set defects policy: {e}")
            return False

    async def set_certification(
        self, simulation_id: str, has_certification: bool
    ) -> bool:
        """
        Установить наличие сертификации.

        Args:
            simulation_id: ID симуляции
            has_certification: Есть ли сертификация

        Returns:
            bool: True если успешно
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                await self._with_retry(
                    self.stub.set_has_certification,
                    simulator_pb2.SetHasCertificationRequest(
                        simulation_id=simulation_id, has_certification=has_certification
                    ),
                )
                status = "with" if has_certification else "without"
                logger.info(f"Set simulation {simulation_id} {status} certification")
                return True

        except grpc.RpcError as e:
            logger.error(f"Failed to set certification: {e}")
            return False

    async def add_production_improvement(
        self, simulation_id: str, improvement: str
    ) -> bool:
        """
        Добавить улучшение производства.

        Args:
            simulation_id: ID симуляции
            improvement: Улучшение производства

        Returns:
            bool: True если успешно
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                await self._with_retry(
                    self.stub.add_production_improvement,
                    simulator_pb2.AddProductionImprovementRequest(
                        simulation_id=simulation_id, production_improvement=improvement
                    ),
                )
                logger.info(
                    f"Added improvement {improvement} to simulation {simulation_id}"
                )
                return True

        except grpc.RpcError as e:
            logger.error(f"Failed to add production improvement: {e}")
            return False

    async def set_sales_strategy(self, simulation_id: str, strategy: str) -> bool:
        """
        Установить стратегию продаж.

        Args:
            simulation_id: ID симуляции
            strategy: Стратегия продаж

        Returns:
            bool: True если успешно
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                await self._with_retry(
                    self.stub.set_sales_strategy,
                    simulator_pb2.SetSalesStrategyRequest(
                        simulation_id=simulation_id, sales_strategy=strategy
                    ),
                )
                logger.info(
                    f"Set sales strategy to {strategy} for simulation {simulation_id}"
                )
                return True

        except grpc.RpcError as e:
            logger.error(f"Failed to set sales strategy: {e}")
            return False
