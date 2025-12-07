from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from datetime import datetime
import uuid


class WarehouseType(str, Enum):
    """Типы складов."""

    UNSPECIFIED = "WAREHOUSE_TYPE_UNSPECIFIED"
    MATERIALS = "WAREHOUSE_TYPE_MATERIALS"
    PRODUCTS = "WAREHOUSE_TYPE_PRODUCTS"


class SupplierModel(BaseModel):
    """Модель поставщика."""

    supplier_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    product_name: str
    delivery_period: int = Field(ge=1, description="Стандартный срок доставки")
    special_delivery_period: int = Field(ge=1, description="Срочный срок доставки")
    reliability: float = Field(ge=0.0, le=1.0, description="Надежность поставщика")
    product_quality: float = Field(ge=0.0, le=1.0, description="Качество продукции")
    cost: int = Field(ge=0, description="Стоимость поставки")
    special_delivery_cost: int = Field(ge=0, description="Стоимость срочной доставки")

    model_config = ConfigDict(from_attributes=True)

    @validator("special_delivery_period")
    def validate_special_delivery(cls, v, values):
        if "delivery_period" in values and v >= values["delivery_period"]:
            raise ValueError("Срочная доставка должна быть быстрее стандартной")
        return v

    @validator("special_delivery_cost")
    def validate_special_cost(cls, v, values):
        if "cost" in values and v <= values["cost"]:
            raise ValueError("Срочная доставка должна стоить дороже")
        return v


class WorkerModel(BaseModel):
    """Модель работника."""

    worker_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    qualification: int = Field(ge=1, le=9, description="Квалификация (1-9)")
    specialty: str
    salary: int = Field(ge=0, description="Зарплата")

    model_config = ConfigDict(from_attributes=True)


class LogistModel(WorkerModel):
    """Модель логиста."""

    speed: int = Field(ge=1, description="Скорость работы")
    vehicle_type: str = Field(description="Тип транспорта")


class EquipmentModel(BaseModel):
    """Модель оборудования."""

    equipment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    reliability: float = Field(ge=0.0, le=1.0, description="Надежность оборудования")
    maintenance_period: int = Field(ge=1, description="Период ТО (дни)")
    maintenance_cost: int = Field(ge=0, description="Стоимость ТО")
    cost: int = Field(ge=0, description="Стоимость покупки")
    repair_cost: int = Field(ge=0, description="Стоимость ремонта")
    repair_time: int = Field(ge=0, description="Время ремонта (дни)")

    model_config = ConfigDict(from_attributes=True)


class WarehouseModel(BaseModel):
    """Модель склада."""

    warehouse_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    size: int = Field(ge=1, description="Общий размер склада")
    loading: int = Field(ge=0, description="Текущая загрузка")
    materials: Dict[str, int] = Field(
        default_factory=dict, description="Материалы на складе"
    )

    model_config = ConfigDict(from_attributes=True)

    @property
    def available_space(self) -> int:
        """Доступное место на складе."""
        return max(0, self.size - self.loading)


class ConsumerModel(BaseModel):
    """Модель заказчика."""

    consumer_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str = Field(description="Тип компании (гос./не гос.)")

    model_config = ConfigDict(from_attributes=True)


class TenderModel(BaseModel):
    """Модель тендера."""

    tender_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    consumer: ConsumerModel
    cost: int = Field(ge=0, description="Стоимость тендера")
    quantity_of_products: int = Field(ge=1, description="Количество изделий")

    model_config = ConfigDict(from_attributes=True)

    @property
    def price_per_unit(self) -> float:
        """Цена за единицу продукции."""
        return self.cost / self.quantity_of_products


class SimulationConfig(BaseModel):
    """Конфигурация симуляции."""

    simulation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    logist: Optional[LogistModel] = None
    suppliers: List[SupplierModel] = Field(default_factory=list)
    backup_suppliers: List[SupplierModel] = Field(default_factory=list)
    materials_warehouse: Optional[WarehouseModel] = None
    product_warehouse: Optional[WarehouseModel] = None
    dealing_with_defects: str = "standard"
    has_certification: bool = False
    production_improvements: List[str] = Field(default_factory=list)
    sales_strategy: str = "standard"

    model_config = ConfigDict(from_attributes=True)


class SimulationResults(BaseModel):
    """Результаты симуляции."""

    profit: int
    cost: int
    profitability: float
    capital: int
    step: int
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)

    @property
    def roi(self) -> float:
        """Return on Investment."""
        return self.profitability * 100

    @property
    def net_profit(self) -> int:
        """Чистая прибыль."""
        return self.profit - self.cost
