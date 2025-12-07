import asyncio
import grpc
from typing import Optional, List, Dict, Any
import logging

from .base_client import AsyncBaseClient
from .proto import simulator_pb2
from .proto import simulator_pb2_grpc
from .models import *
from .exceptions import *

logger = logging.getLogger(__name__)


class AsyncDatabaseClient(AsyncBaseClient):
    """
    Асинхронный клиент для SimulationDatabaseManager.

    Работает на порту 50052 (или другом указанном порту).

    Пример использования:
    ```python
    async with AsyncDatabaseClient("localhost", 50052) as client:
        suppliers = await client.get_all_suppliers()
        workers = await client.get_all_workers()
        equipment = await client.get_all_equipment()
    ```
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 50052,  # 👈 Порт для DatabaseManager (отличается!)
        max_retries: int = 3,
        timeout: float = 30.0,
        rate_limit: Optional[float] = None,
        enable_logging: bool = True,
    ):
        super().__init__(host, port, max_retries, timeout, rate_limit, enable_logging)
        self.stub = None

    async def connect(self):
        """Подключиться к серверу SimulationDatabaseManager."""
        try:
            self.channel = await self._create_channel()
            self.stub = simulator_pb2_grpc.SimulationDatabaseManagerStub(self.channel)

            # Проверяем соединение
            if await self.ping():
                logger.info(f"Connected to DatabaseManager at {self.host}:{self.port}")
            else:
                raise ConnectionError(
                    f"Cannot connect to DatabaseManager at {self.host}:{self.port}"
                )

        except Exception as e:
            logger.error(f"Failed to connect to DatabaseManager: {e}")
            raise ConnectionError(f"Connection to DatabaseManager failed: {e}")

    async def close(self):
        """Закрыть соединение."""
        if self.channel:
            await self.channel.close()
            logger.info("Disconnected from DatabaseManager")

    async def ping(self) -> bool:
        """
        Проверить доступность DatabaseManager.

        Returns:
            bool: True если сервер доступен
        """
        try:
            async with self._timeout_context(5.0):
                await self._rate_limit()
                response = await self.stub.ping(simulator_pb2.PingRequest())
                return response.success
        except Exception as e:
            logger.warning(f"Ping to DatabaseManager failed: {e}")
            return False

    # ==================== Управление поставщиками ====================

    async def get_all_suppliers(self) -> List[SupplierModel]:
        """
        Получить всех поставщиков.

        Returns:
            List[SupplierModel]: Список поставщиков
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                response = await self._with_retry(
                    self.stub.get_all_suppliers, simulator_pb2.GetAllSuppliersRequest()
                )

                return [
                    SupplierModel(
                        supplier_id=s.supplier_id,
                        name=s.name,
                        product_name=s.product_name,
                        delivery_period=s.delivery_period,
                        special_delivery_period=s.special_delivery_period,
                        reliability=s.reliability,
                        product_quality=s.product_quality,
                        cost=s.cost,
                        special_delivery_cost=s.special_delivery_cost,
                    )
                    for s in response.suppliers
                ]

        except grpc.RpcError as e:
            self._handle_grpc_error(e, "Get all suppliers")

    async def create_supplier(self, supplier: SupplierModel) -> SupplierModel:
        """
        Создать нового поставщика.

        Args:
            supplier: Модель поставщика

        Returns:
            SupplierModel: Созданный поставщик
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                request = simulator_pb2.CreateSupplierRequest(
                    name=supplier.name,
                    product_name=supplier.product_name,
                    delivery_period=supplier.delivery_period,
                    special_delivery_period=supplier.special_delivery_period,
                    reliability=supplier.reliability,
                    product_quality=supplier.product_quality,
                    cost=supplier.cost,
                    special_delivery_cost=supplier.special_delivery_cost,
                )

                response = await self._with_retry(self.stub.create_supplier, request)

                return SupplierModel(
                    supplier_id=response.supplier_id,
                    name=response.name,
                    product_name=response.product_name,
                    delivery_period=response.delivery_period,
                    special_delivery_period=response.special_delivery_period,
                    reliability=response.reliability,
                    product_quality=response.product_quality,
                    cost=response.cost,
                    special_delivery_cost=response.special_delivery_cost,
                )

        except grpc.RpcError as e:
            self._handle_grpc_error(e, "Create supplier")

    # ==================== Управление работниками ====================

    async def get_all_workers(self) -> List[WorkerModel]:
        """
        Получить всех работников.

        Returns:
            List[WorkerModel]: Список работников
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                response = await self._with_retry(
                    self.stub.get_all_workers, simulator_pb2.GetAllWorkersRequest()
                )

                return [
                    WorkerModel(
                        worker_id=w.worker_id,
                        name=w.name,
                        qualification=w.qualification,
                        specialty=w.specialty,
                        salary=w.salary,
                    )
                    for w in response.workers
                ]

        except grpc.RpcError as e:
            self._handle_grpc_error(e, "Get all workers")

    async def get_all_logists(self) -> List[LogistModel]:
        """
        Получить всех логистов.

        Returns:
            List[LogistModel]: Список логистов
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                response = await self._with_retry(
                    self.stub.get_all_logists, simulator_pb2.GetAllLogistsRequest()
                )

                return [
                    LogistModel(
                        worker_id=l.worker_id,
                        name=l.name,
                        qualification=l.qualification,
                        specialty=l.specialty,
                        salary=l.salary,
                        speed=l.speed,
                        vehicle_type=l.vehicle_type,
                    )
                    for l in response.logists
                ]

        except grpc.RpcError as e:
            self._handle_grpc_error(e, "Get all logists")

    async def create_worker(self, worker: WorkerModel) -> WorkerModel:
        """
        Создать нового работника.

        Args:
            worker: Модель работника

        Returns:
            WorkerModel: Созданный работник
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                request = simulator_pb2.CreateWorkerRequest(
                    name=worker.name,
                    qualification=worker.qualification,
                    specialty=worker.specialty,
                    salary=worker.salary,
                )

                response = await self._with_retry(self.stub.create_worker, request)

                return WorkerModel(
                    worker_id=response.worker_id,
                    name=response.name,
                    qualification=response.qualification,
                    specialty=response.specialty,
                    salary=response.salary,
                )

        except grpc.RpcError as e:
            self._handle_grpc_error(e, "Create worker")

    async def create_logist(self, logist: LogistModel) -> LogistModel:
        """
        Создать нового логиста.

        Args:
            logist: Модель логиста

        Returns:
            LogistModel: Созданный логист
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                request = simulator_pb2.CreateLogistRequest(
                    name=logist.name,
                    qualification=logist.qualification,
                    specialty=logist.specialty,
                    salary=logist.salary,
                    speed=logist.speed,
                    vehicle_type=logist.vehicle_type,
                )

                response = await self._with_retry(self.stub.create_logist, request)

                return LogistModel(
                    worker_id=response.worker_id,
                    name=response.name,
                    qualification=response.qualification,
                    specialty=response.specialty,
                    salary=response.salary,
                    speed=response.speed,
                    vehicle_type=response.vehicle_type,
                )

        except grpc.RpcError as e:
            self._handle_grpc_error(e, "Create logist")

    # ==================== Управление оборудованием ====================

    async def get_all_equipment(self) -> List[EquipmentModel]:
        """
        Получить всё оборудование.

        Returns:
            List[EquipmentModel]: Список оборудования
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                response = await self._with_retry(
                    self.stub.get_all_equipment, simulator_pb2.GetAllEquipmentRequest()
                )

                return [
                    EquipmentModel(
                        equipment_id=e.equipment_id,
                        name=e.name,
                        reliability=e.reliability,
                        maintenance_period=e.maintenance_period,
                        maintenance_cost=e.maintenance_cost,
                        cost=e.cost,
                        repair_cost=e.repair_cost,
                        repair_time=e.repair_time,
                    )
                    for e in response.equipments
                ]

        except grpc.RpcError as e:
            self._handle_grpc_error(e, "Get all equipment")

    async def create_equipment(self, equipment: EquipmentModel) -> EquipmentModel:
        """
        Создать новое оборудование.

        Args:
            equipment: Модель оборудования

        Returns:
            EquipmentModel: Созданное оборудование
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                request = simulator_pb2.CreateEquipmentRequest(
                    name=equipment.name,
                    reliability=equipment.reliability,
                    maintenance_period=equipment.maintenance_period,
                    maintenance_cost=equipment.maintenance_cost,
                    cost=equipment.cost,
                    repair_cost=equipment.repair_cost,
                    repair_time=equipment.repair_time,
                )

                response = await self._with_retry(self.stub.create_equipment, request)

                return EquipmentModel(
                    equipment_id=response.equipment_id,
                    name=response.name,
                    reliability=response.reliability,
                    maintenance_period=response.maintenance_period,
                    maintenance_cost=response.maintenance_cost,
                    cost=response.cost,
                    repair_cost=response.repair_cost,
                    repair_time=response.repair_time,
                )

        except grpc.RpcError as e:
            self._handle_grpc_error(e, "Create equipment")

    # ==================== Управление тендерами ====================

    async def get_all_tenders(self) -> List[TenderModel]:
        """
        Получить все тендеры.

        Returns:
            List[TenderModel]: Список тендеров
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                response = await self._with_retry(
                    self.stub.get_all_tenders, simulator_pb2.GetAllTendersRequest()
                )

                return [
                    TenderModel(
                        tender_id=t.tender_id,
                        consumer=ConsumerModel(
                            consumer_id=t.consumer.consumer_id,
                            name=t.consumer.name,
                            type=t.consumer.type,
                        ),
                        cost=t.cost,
                        quantity_of_products=t.quantity_of_products,
                    )
                    for t in response.tenders
                ]

        except grpc.RpcError as e:
            self._handle_grpc_error(e, "Get all tenders")

    async def create_tender(self, tender: TenderModel) -> TenderModel:
        """
        Создать новый тендер.

        Args:
            tender: Модель тендера

        Returns:
            TenderModel: Созданный тендер
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                request = simulator_pb2.CreateTenderRequest(
                    consumer_id=tender.consumer.consumer_id,
                    cost=tender.cost,
                    quantity_of_products=tender.quantity_of_products,
                )

                response = await self._with_retry(self.stub.create_tender, request)

                return TenderModel(
                    tender_id=response.tender_id,
                    consumer=ConsumerModel(
                        consumer_id=response.consumer.consumer_id,
                        name=response.consumer.name,
                        type=response.consumer.type,
                    ),
                    cost=response.cost,
                    quantity_of_products=response.quantity_of_products,
                )

        except grpc.RpcError as e:
            self._handle_grpc_error(e, "Create tender")

    # ==================== Дополнительные методы ====================

    async def get_warehouse(self, warehouse_id: str) -> WarehouseModel:
        """
        Получить информацию о складе.

        Args:
            warehouse_id: ID склада

        Returns:
            WarehouseModel: Модель склада
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                response = await self._with_retry(
                    self.stub.get_warehouse,
                    simulator_pb2.GetWarehouseRequest(warehouse_id=warehouse_id),
                )

                return WarehouseModel(
                    warehouse_id=response.warehouse_id,
                    size=response.size,
                    loading=response.loading,
                    materials=dict(response.materials),
                )

        except grpc.RpcError as e:
            self._handle_grpc_error(e, "Get warehouse")

    async def get_all_consumers(self) -> List[ConsumerModel]:
        """
        Получить всех заказчиков.

        Returns:
            List[ConsumerModel]: Список заказчиков
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                response = await self._with_retry(
                    self.stub.get_all_consumers, simulator_pb2.GetAllConsumersRequest()
                )

                return [
                    ConsumerModel(consumer_id=c.consumer_id, name=c.name, type=c.type)
                    for c in response.consumers
                ]

        except grpc.RpcError as e:
            self._handle_grpc_error(e, "Get all consumers")

    async def get_all_workplaces(self) -> List[Dict[str, Any]]:
        """
        Получить все рабочие места.

        Returns:
            List[Dict]: Список рабочих мест
        """
        try:
            async with self._timeout_context():
                await self._rate_limit()
                response = await self._with_retry(
                    self.stub.get_all_workplaces,
                    simulator_pb2.GetAllWorkplacesRequest(),
                )

                workplaces = []
                for wp in response.workplaces:
                    workplace_dict = {
                        "workplace_id": wp.workplace_id,
                        "workplace_name": wp.workplace_name,
                        "required_speciality": wp.required_speciality,
                        "required_qualification": wp.required_qualification,
                        "required_stages": list(wp.required_stages),
                    }

                    if wp.worker.worker_id:
                        workplace_dict["worker"] = {
                            "worker_id": wp.worker.worker_id,
                            "name": wp.worker.name,
                        }

                    if wp.equipment.equipment_id:
                        workplace_dict["equipment"] = {
                            "equipment_id": wp.equipment.equipment_id,
                            "name": wp.equipment.name,
                        }

                    workplaces.append(workplace_dict)

                return workplaces

        except grpc.RpcError as e:
            self._handle_grpc_error(e, "Get all workplaces")
