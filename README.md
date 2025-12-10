# Industrial Digital Polygon Simulator Client

Асинхронный Python-клиент для работы с сервисами симуляции промышленного цифрового полигона. Клиент предоставляет удобный интерфейс для взаимодействия с двумя gRPC сервисами: SimulationService и SimulationDatabaseManager.

## Установка

```bash
poetry install
```

## Основные компоненты

Библиотека предоставляет три основных клиента:

1. **AsyncUnifiedClient** - объединенный клиент для работы с обоими сервисами (рекомендуется)
2. **AsyncSimulationClient** - клиент для работы с сервисом симуляции (порт 50051)
3. **AsyncDatabaseClient** - клиент для работы с сервисом базы данных (порт 50052)

## Быстрый старт

```python
import asyncio
from simulation_client import AsyncUnifiedClient

async def main():
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
        simulation_config = await client.create_simulation()
        await client.configure_simulation(
            simulation_id=simulation_config.simulation_id,
            logist_id=logists.logists[0].worker_id if logists.logists else None,
            supplier_ids=[s.supplier_id for s in suppliers.suppliers[:2]]
        )
        
        # Запускаем симуляцию
        response = await client.run_simulation(simulation_config.simulation_id)
        results = response.simulation.results
        print(f"Прибыль: {results.profit:,} ₽")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## AsyncUnifiedClient

Объединенный клиент, который предоставляет единый интерфейс для работы с обоими сервисами. Это фасад, скрывающий сложность работы с двумя разными сервисами.

### Инициализация

```python
client = AsyncUnifiedClient(
    sim_host: str = "localhost",      # Хост сервиса симуляции
    sim_port: int = 50051,             # Порт сервиса симуляции
    db_host: str = "localhost",        # Хост сервиса базы данных
    db_port: int = 50052,              # Порт сервиса базы данных
    max_retries: int = 3,              # Максимальное количество повторных попыток
    timeout: float = 30.0,             # Таймаут операций в секундах
    rate_limit: Optional[float] = None,  # Ограничение запросов в секунду
    enable_logging: bool = True,       # Включить логирование
)
```

### Методы подключения

#### `async def connect() -> None`
Подключиться к обоим сервисам параллельно.

#### `async def close() -> None`
Закрыть соединения с обоими сервисами.

#### `async def ping() -> Dict[str, bool]`
Проверить доступность всех сервисов.

**Returns:**
```python
{
    "simulation_service": bool,
    "database_service": bool
}
```

---

## Методы работы с симуляцией

### Создание и получение симуляций

#### `async def create_simulation() -> SimulationConfig`
Создать новую симуляцию.

**Returns:** `SimulationConfig` - конфигурация созданной симуляции с `simulation_id`

**Пример:**
```python
config = await client.create_simulation()
print(f"Создана симуляция: {config.simulation_id}")
```

#### `async def get_simulation(simulation_id: str) -> SimulationResponse`
Получить полную информацию о симуляции.

**Parameters:**
- `simulation_id: str` - ID симуляции

**Returns:** `SimulationResponse` - полный ответ с симуляцией, параметрами и результатами

#### `async def get_simulation_as_dict(simulation_id: str) -> Dict[str, Any]`
Получить информацию о симуляции в виде словаря.

**Parameters:**
- `simulation_id: str` - ID симуляции

**Returns:** `Dict[str, Any]` - информация о симуляции в виде словаря

### Запуск симуляции

#### `async def run_simulation(simulation_id: str) -> SimulationResponse`
Запустить симуляцию и получить полный ответ с результатами.

**Parameters:**
- `simulation_id: str` - ID симуляции

**Returns:** `SimulationResponse` - полный ответ с результатами симуляции

**Пример:**
```python
response = await client.run_simulation(simulation_id)
results = response.simulation.results
print(f"Прибыль: {results.profit}")
print(f"ROI: {results.roi:.2f}%")
```

#### `async def run_simulation_and_get_results(simulation_id: str) -> SimulationResults`
Запустить симуляцию и получить только результаты (без полной информации о симуляции).

**Parameters:**
- `simulation_id: str` - ID симуляции

**Returns:** `SimulationResults` - результаты симуляции

#### `async def run_simulation_step(simulation_id: str, step_count: int = 1) -> SimulationStepResponse`
Запустить один или несколько шагов симуляции.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `step_count: int` - количество шагов (по умолчанию 1)

**Returns:** `SimulationStepResponse` - ответ с результатами шага и метриками

---

## Методы настройки симуляции

### Управление логистом

#### `async def set_logist(simulation_id: str, worker_id: str) -> SimulationResponse`
Назначить логиста для симуляции.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `worker_id: str` - ID работника-логиста

**Returns:** `SimulationResponse` - обновленная симуляция

### Управление поставщиками

#### `async def add_supplier(simulation_id: str, supplier_id: str, is_backup: bool = False) -> SimulationResponse`
Добавить поставщика в симуляцию.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `supplier_id: str` - ID поставщика
- `is_backup: bool` - является ли запасным поставщиком (по умолчанию False)

**Returns:** `SimulationResponse` - обновленная симуляция

#### `async def delete_supplier(simulation_id: str, supplier_id: str) -> SimulationResponse`
Удалить поставщика из симуляции.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `supplier_id: str` - ID поставщика

**Returns:** `SimulationResponse` - обновленная симуляция

### Управление складами

#### `async def set_warehouse_worker(simulation_id: str, worker_id: str, warehouse_type: WarehouseType) -> SimulationResponse`
Назначить работника на склад.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `worker_id: str` - ID работника
- `warehouse_type: WarehouseType` - тип склада (WAREHOUSE_TYPE_MATERIALS или WAREHOUSE_TYPE_PRODUCTS)

**Returns:** `SimulationResponse` - обновленная симуляция

#### `async def increase_warehouse_size(simulation_id: str, warehouse_type: WarehouseType, size: int) -> SimulationResponse`
Увеличить размер склада.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `warehouse_type: WarehouseType` - тип склада
- `size: int` - на сколько увеличить

**Returns:** `SimulationResponse` - обновленная симуляция

### Управление рабочими местами

#### `async def set_worker_on_workplace(simulation_id: str, worker_id: str, workplace_id: str) -> SimulationResponse`
Назначить работника на рабочее место.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `worker_id: str` - ID работника
- `workplace_id: str` - ID рабочего места

**Returns:** `SimulationResponse` - обновленная симуляция

#### `async def unset_worker_on_workplace(simulation_id: str, worker_id: str) -> SimulationResponse`
Снять работника с рабочего места.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `worker_id: str` - ID работника

**Returns:** `SimulationResponse` - обновленная симуляция

#### `async def set_equipment_on_workplace(simulation_id: str, workplace_id: str, equipment_id: str) -> SimulationResponse`
Установить оборудование на рабочее место.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `workplace_id: str` - ID рабочего места
- `equipment_id: str` - ID оборудования

**Returns:** `SimulationResponse` - обновленная симуляция

#### `async def unset_equipment_on_workplace(simulation_id: str, workplace_id: str) -> SimulationResponse`
Снять оборудование с рабочего места.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `workplace_id: str` - ID рабочего места

**Returns:** `SimulationResponse` - обновленная симуляция

### Управление тендерами

#### `async def add_tender(simulation_id: str, tender_id: str) -> SimulationResponse`
Добавить тендер в симуляцию.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `tender_id: str` - ID тендера

**Returns:** `SimulationResponse` - обновленная симуляция

#### `async def delete_tender(simulation_id: str, tender_id: str) -> SimulationResponse`
Удалить тендер из симуляции.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `tender_id: str` - ID тендера

**Returns:** `SimulationResponse` - обновленная симуляция

### Настройка политик и стратегий

#### `async def set_dealing_with_defects(simulation_id: str, policy: str) -> SimulationResponse`
Установить политику работы с браком.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `policy: str` - политика работы с браком

**Returns:** `SimulationResponse` - обновленная симуляция

#### `async def set_certification(simulation_id: str, has_certification: bool) -> SimulationResponse`
Установить наличие сертификации.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `has_certification: bool` - есть ли сертификация

**Returns:** `SimulationResponse` - обновленная симуляция

#### `async def set_sales_strategy(simulation_id: str, strategy: str) -> SimulationResponse`
Установить стратегию продаж.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `strategy: str` - стратегия продаж

**Returns:** `SimulationResponse` - обновленная симуляция

#### `async def set_sales_strategy_with_details(simulation_id: str, strategy: str, growth_forecast: float = 0.0, unit_cost: int = 0, market_impact: str = "", trend_direction: str = "") -> SimulationResponse`
Установить стратегию продаж с деталями.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `strategy: str` - стратегия продаж
- `growth_forecast: float` - прогноз роста
- `unit_cost: int` - стоимость единицы
- `market_impact: str` - влияние на рынок
- `trend_direction: str` - направление тренда

**Returns:** `SimulationResponse` - обновленная симуляция

### Управление улучшениями производства

#### `async def add_production_improvement(simulation_id: str, improvement: str) -> SimulationResponse`
Добавить улучшение производства.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `improvement: str` - улучшение производства

**Returns:** `SimulationResponse` - обновленная симуляция

#### `async def delete_production_improvement(simulation_id: str, improvement: str) -> SimulationResponse`
Удалить улучшение производства.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `improvement: str` - улучшение производства

**Returns:** `SimulationResponse` - обновленная симуляция

### Управление графом процесса

#### `async def add_process_route(simulation_id: str, length: int, from_workplace: str, to_workplace: str) -> SimulationResponse`
Добавить маршрут процесса.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `length: int` - длина маршрута
- `from_workplace: str` - ID начального рабочего места
- `to_workplace: str` - ID конечного рабочего места

**Returns:** `SimulationResponse` - обновленная симуляция

#### `async def delete_process_route(simulation_id: str, from_workplace: str, to_workplace: str) -> SimulationResponse`
Удалить маршрут процесса.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `from_workplace: str` - ID начального рабочего места
- `to_workplace: str` - ID конечного рабочего места

**Returns:** `SimulationResponse` - обновленная симуляция

#### `async def configure_workplace_in_graph(simulation_id: str, workplace_id: str, workplace_type: str, worker_id: Optional[str] = None, equipment_id: Optional[str] = None, is_start_node: bool = False, is_end_node: bool = False, next_workplace_ids: Optional[List[str]] = None) -> SimulationResponse`
Настроить рабочее место в графе процесса.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `workplace_id: str` - ID рабочего места
- `workplace_type: str` - тип рабочего места
- `worker_id: Optional[str]` - ID работника (опционально)
- `equipment_id: Optional[str]` - ID оборудования (опционально)
- `is_start_node: bool` - является ли начальным узлом
- `is_end_node: bool` - является ли конечным узлом
- `next_workplace_ids: Optional[List[str]]` - список ID следующих рабочих мест

**Returns:** `SimulationResponse` - обновленная симуляция

#### `async def remove_workplace_from_graph(simulation_id: str, workplace_id: str) -> SimulationResponse`
Удалить рабочее место из графа процесса.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `workplace_id: str` - ID рабочего места

**Returns:** `SimulationResponse` - обновленная симуляция

#### `async def set_workplace_as_start_node(simulation_id: str, workplace_id: str) -> SimulationResponse`
Установить рабочее место как начальный узел.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `workplace_id: str` - ID рабочего места

**Returns:** `SimulationResponse` - обновленная симуляция

#### `async def set_workplace_as_end_node(simulation_id: str, workplace_id: str) -> SimulationResponse`
Установить рабочее место как конечный узел.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `workplace_id: str` - ID рабочего места

**Returns:** `SimulationResponse` - обновленная симуляция

#### `async def update_process_graph(simulation_id: str, process_graph: ProcessGraph) -> SimulationResponse`
Обновить граф процесса.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `process_graph: ProcessGraph` - граф процесса

**Returns:** `SimulationResponse` - обновленная симуляция

### Управление производственным планом

#### `async def distribute_production_plan(simulation_id: str, strategy: DistributionStrategy, auto_assign_workers: bool = False, auto_assign_equipment: bool = False) -> ProductionPlanDistributionResponse`
Распределить производственный план.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `strategy: DistributionStrategy` - стратегия распределения
- `auto_assign_workers: bool` - автоматически назначить работников
- `auto_assign_equipment: bool` - автоматически назначить оборудование

**Returns:** `ProductionPlanDistributionResponse` - распределение плана

#### `async def get_production_plan_distribution(simulation_id: str) -> ProductionPlanDistributionResponse`
Получить распределение производственного плана.

**Parameters:**
- `simulation_id: str` - ID симуляции

**Returns:** `ProductionPlanDistributionResponse` - распределение плана

#### `async def update_production_assignment(simulation_id: str, assignment: ProductionPlanAssignment) -> SimulationResponse`
Обновить назначение производства.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `assignment: ProductionPlanAssignment` - назначение производства

**Returns:** `SimulationResponse` - обновленная симуляция

#### `async def update_workshop_plan(simulation_id: str, workshop_plan: WorkshopPlan) -> SimulationResponse`
Обновить план цеха.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `workshop_plan: WorkshopPlan` - план цеха

**Returns:** `SimulationResponse` - обновленная симуляция

#### `async def get_production_schedule(simulation_id: str) -> ProductionScheduleResponse`
Получить производственный план.

**Parameters:**
- `simulation_id: str` - ID симуляции

**Returns:** `ProductionScheduleResponse` - производственный план

#### `async def update_production_schedule(simulation_id: str, schedule: ProductionSchedule) -> SimulationResponse`
Обновить производственный план.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `schedule: ProductionSchedule` - производственный план

**Returns:** `SimulationResponse` - обновленная симуляция

#### `async def get_workshop_plan(simulation_id: str) -> WorkshopPlanResponse`
Получить план цеха.

**Parameters:**
- `simulation_id: str` - ID симуляции

**Returns:** `WorkshopPlanResponse` - план цеха

### Дополнительные настройки

#### `async def set_quality_inspection(simulation_id: str, material_id: str, inspection: QualityInspection) -> SimulationResponse`
Установить контроль качества.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `material_id: str` - ID материала
- `inspection: QualityInspection` - настройки контроля качества

**Returns:** `SimulationResponse` - обновленная симуляция

#### `async def set_delivery_schedule(simulation_id: str, supplier_id: str, schedule: DeliverySchedule) -> SimulationResponse`
Установить график поставок.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `supplier_id: str` - ID поставщика
- `schedule: DeliverySchedule` - график поставок

**Returns:** `SimulationResponse` - обновленная симуляция

#### `async def set_equipment_maintenance_interval(simulation_id: str, equipment_id: str, interval_days: int) -> SimulationResponse`
Установить интервал обслуживания оборудования.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `equipment_id: str` - ID оборудования
- `interval_days: int` - интервал в днях

**Returns:** `SimulationResponse` - обновленная симуляция

#### `async def set_certification_status(simulation_id: str, certificate_type: str, is_obtained: bool) -> SimulationResponse`
Установить статус сертификации.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `certificate_type: str` - тип сертификата
- `is_obtained: bool` - получен ли сертификат

**Returns:** `SimulationResponse` - обновленная симуляция

#### `async def set_lean_improvement_status(simulation_id: str, improvement_id: str, is_implemented: bool) -> SimulationResponse`
Установить статус улучшения Lean.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `improvement_id: str` - ID улучшения
- `is_implemented: bool` - реализовано ли улучшение

**Returns:** `SimulationResponse` - обновленная симуляция

---

## Методы получения метрик

### Получение различных метрик

#### `async def get_factory_metrics(simulation_id: str, step: Optional[int] = None) -> FactoryMetricsResponse`
Получить метрики завода.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `step: Optional[int]` - шаг симуляции (опционально)

**Returns:** `FactoryMetricsResponse` - метрики завода (прибыльность, OEE, загрузка складов и т.д.)

#### `async def get_production_metrics(simulation_id: str, step: Optional[int] = None) -> ProductionMetricsResponse`
Получить метрики производства.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `step: Optional[int]` - шаг симуляции (опционально)

**Returns:** `ProductionMetricsResponse` - метрики производства (производительность, использование оборудования и т.д.)

#### `async def get_quality_metrics(simulation_id: str, step: Optional[int] = None) -> QualityMetricsResponse`
Получить метрики качества.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `step: Optional[int]` - шаг симуляции (опционально)

**Returns:** `QualityMetricsResponse` - метрики качества (процент брака, причины брака и т.д.)

#### `async def get_engineering_metrics(simulation_id: str, step: Optional[int] = None) -> EngineeringMetricsResponse`
Получить метрики инженерии.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `step: Optional[int]` - шаг симуляции (опционально)

**Returns:** `EngineeringMetricsResponse` - метрики инженерии (время операций, простои и т.д.)

#### `async def get_commercial_metrics(simulation_id: str, step: Optional[int] = None) -> CommercialMetricsResponse`
Получить метрики коммерции.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `step: Optional[int]` - шаг симуляции (опционально)

**Returns:** `CommercialMetricsResponse` - метрики коммерции (выручка, тендеры и т.д.)

#### `async def get_procurement_metrics(simulation_id: str, step: Optional[int] = None) -> ProcurementMetricsResponse`
Получить метрики закупок.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `step: Optional[int]` - шаг симуляции (опционально)

**Returns:** `ProcurementMetricsResponse` - метрики закупок (производительность поставщиков и т.д.)

#### `async def get_all_metrics(simulation_id: str) -> AllMetricsResponse`
Получить все метрики одновременно.

**Parameters:**
- `simulation_id: str` - ID симуляции

**Returns:** `AllMetricsResponse` - все метрики (завод, производство, качество, инженерия, коммерция, закупки)

### Дополнительная информация

#### `async def get_unplanned_repair(simulation_id: str) -> UnplannedRepairResponse`
Получить информацию о внеплановых ремонтах.

**Parameters:**
- `simulation_id: str` - ID симуляции

**Returns:** `UnplannedRepairResponse` - информация о внеплановых ремонтах

#### `async def get_warehouse_load_chart(simulation_id: str, warehouse_id: str) -> WarehouseLoadChartResponse`
Получить график загрузки склада.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `warehouse_id: str` - ID склада

**Returns:** `WarehouseLoadChartResponse` - график загрузки склада

#### `async def get_required_materials(simulation_id: str) -> RequiredMaterialsResponse`
Получить список требуемых материалов.

**Parameters:**
- `simulation_id: str` - ID симуляции

**Returns:** `RequiredMaterialsResponse` - список требуемых материалов

#### `async def get_available_improvements(simulation_id: str) -> AvailableImprovementsResponse`
Получить доступные улучшения для симуляции.

**Parameters:**
- `simulation_id: str` - ID симуляции

**Returns:** `AvailableImprovementsResponse` - список доступных улучшений

#### `async def get_defect_policies(simulation_id: str) -> DefectPoliciesResponse`
Получить политики работы с браком.

**Parameters:**
- `simulation_id: str` - ID симуляции

**Returns:** `DefectPoliciesResponse` - политики работы с браком

#### `async def get_simulation_history(simulation_id: str) -> SimulationHistoryResponse`
Получить историю симуляции (все шаги).

**Parameters:**
- `simulation_id: str` - ID симуляции

**Returns:** `SimulationHistoryResponse` - история симуляции

#### `async def validate_configuration(simulation_id: str) -> ValidationResponse`
Валидировать конфигурацию симуляции.

**Parameters:**
- `simulation_id: str` - ID симуляции

**Returns:** `ValidationResponse` - результат валидации с ошибками и предупреждениями

---

## Методы работы с базой данных

### Управление поставщиками

#### `async def get_all_suppliers() -> GetAllSuppliersResponse`
Получить всех поставщиков.

**Returns:** `GetAllSuppliersResponse` - список всех поставщиков

#### `async def create_supplier(request: CreateSupplierRequest) -> Supplier`
Создать нового поставщика.

**Parameters:**
- `request: CreateSupplierRequest` - данные поставщика

**Returns:** `Supplier` - созданный поставщик

**Пример:**
```python
from simulation_client.models import CreateSupplierRequest

request = CreateSupplierRequest(
    name="ООО Поставщик",
    product_name="Сталь",
    delivery_period=10,
    special_delivery_period=5,
    reliability=0.95,
    product_quality=0.9,
    cost=10000,
    special_delivery_cost=15000
)
supplier = await client.create_supplier(request)
```

#### `async def update_supplier(request: UpdateSupplierRequest) -> Supplier`
Обновить поставщика.

**Parameters:**
- `request: UpdateSupplierRequest` - данные для обновления

**Returns:** `Supplier` - обновленный поставщик

#### `async def delete_supplier(request: DeleteSupplierRequest) -> SuccessResponse`
Удалить поставщика.

**Parameters:**
- `request: DeleteSupplierRequest` - запрос на удаление

**Returns:** `SuccessResponse` - результат удаления

### Управление работниками

#### `async def get_all_workers() -> GetAllWorkersResponse`
Получить всех работников.

**Returns:** `GetAllWorkersResponse` - список всех работников

#### `async def create_worker(request: CreateWorkerRequest) -> Worker`
Создать нового работника.

**Parameters:**
- `request: CreateWorkerRequest` - данные работника

**Returns:** `Worker` - созданный работник

#### `async def update_worker(request: UpdateWorkerRequest) -> Worker`
Обновить работника.

**Parameters:**
- `request: UpdateWorkerRequest` - данные для обновления

**Returns:** `Worker` - обновленный работник

#### `async def delete_worker(request: DeleteWorkerRequest) -> SuccessResponse`
Удалить работника.

**Parameters:**
- `request: DeleteWorkerRequest` - запрос на удаление

**Returns:** `SuccessResponse` - результат удаления

### Управление логистами

#### `async def get_all_logists() -> GetAllLogistsResponse`
Получить всех логистов.

**Returns:** `GetAllLogistsResponse` - список всех логистов

#### `async def create_logist(request: CreateLogistRequest) -> Logist`
Создать нового логиста.

**Parameters:**
- `request: CreateLogistRequest` - данные логиста

**Returns:** `Logist` - созданный логист

#### `async def update_logist(request: UpdateLogistRequest) -> Logist`
Обновить логиста.

**Parameters:**
- `request: UpdateLogistRequest` - данные для обновления

**Returns:** `Logist` - обновленный логист

#### `async def delete_logist(request: DeleteLogistRequest) -> SuccessResponse`
Удалить логиста.

**Parameters:**
- `request: DeleteLogistRequest` - запрос на удаление

**Returns:** `SuccessResponse` - результат удаления

### Управление оборудованием

#### `async def get_all_equipment() -> GetAllEquipmentResponse`
Получить всё оборудование.

**Returns:** `GetAllEquipmentResponse` - список всего оборудования

#### `async def create_equipment(request: CreateEquipmentRequest) -> Equipment`
Создать новое оборудование.

**Parameters:**
- `request: CreateEquipmentRequest` - данные оборудования

**Returns:** `Equipment` - созданное оборудование

#### `async def update_equipment(request: UpdateEquipmentRequest) -> Equipment`
Обновить оборудование.

**Parameters:**
- `request: UpdateEquipmentRequest` - данные для обновления

**Returns:** `Equipment` - обновленное оборудование

#### `async def delete_equipment(request: DeleteEquipmentRequest) -> SuccessResponse`
Удалить оборудование.

**Parameters:**
- `request: DeleteEquipmentRequest` - запрос на удаление

**Returns:** `SuccessResponse` - результат удаления

### Управление тендерами

#### `async def get_all_tenders() -> GetAllTendersResponse`
Получить все тендеры.

**Returns:** `GetAllTendersResponse` - список всех тендеров

#### `async def create_tender(request: CreateTenderRequest) -> Tender`
Создать новый тендер.

**Parameters:**
- `request: CreateTenderRequest` - данные тендера

**Returns:** `Tender` - созданный тендер

#### `async def update_tender(request: UpdateTenderRequest) -> Tender`
Обновить тендер.

**Parameters:**
- `request: UpdateTenderRequest` - данные для обновления

**Returns:** `Tender` - обновленный тендер

#### `async def delete_tender(request: DeleteTenderRequest) -> SuccessResponse`
Удалить тендер.

**Parameters:**
- `request: DeleteTenderRequest` - запрос на удаление

**Returns:** `SuccessResponse` - результат удаления

### Управление заказчиками

#### `async def get_all_consumers() -> GetAllConsumersResponse`
Получить всех заказчиков.

**Returns:** `GetAllConsumersResponse` - список всех заказчиков

#### `async def create_consumer(request: CreateConsumerRequest) -> Consumer`
Создать нового заказчика.

**Parameters:**
- `request: CreateConsumerRequest` - данные заказчика

**Returns:** `Consumer` - созданный заказчик

#### `async def update_consumer(request: UpdateConsumerRequest) -> Consumer`
Обновить заказчика.

**Parameters:**
- `request: UpdateConsumerRequest` - данные для обновления

**Returns:** `Consumer` - обновленный заказчик

#### `async def delete_consumer(request: DeleteConsumerRequest) -> SuccessResponse`
Удалить заказчика.

**Parameters:**
- `request: DeleteConsumerRequest` - запрос на удаление

**Returns:** `SuccessResponse` - результат удаления

### Управление рабочими местами

#### `async def get_all_workplaces() -> GetAllWorkplacesResponse`
Получить все рабочие места.

**Returns:** `GetAllWorkplacesResponse` - список всех рабочих мест

#### `async def create_workplace(request: CreateWorkplaceRequest) -> Workplace`
Создать новое рабочее место.

**Parameters:**
- `request: CreateWorkplaceRequest` - данные рабочего места

**Returns:** `Workplace` - созданное рабочее место

#### `async def update_workplace(request: UpdateWorkplaceRequest) -> Workplace`
Обновить рабочее место.

**Parameters:**
- `request: UpdateWorkplaceRequest` - данные для обновления

**Returns:** `Workplace` - обновленное рабочее место

#### `async def delete_workplace(request: DeleteWorkplaceRequest) -> SuccessResponse`
Удалить рабочее место.

**Parameters:**
- `request: DeleteWorkplaceRequest` - запрос на удаление

**Returns:** `SuccessResponse` - результат удаления

### Управление складами

#### `async def get_warehouse(request: GetWarehouseRequest) -> Warehouse`
Получить информацию о складе.

**Parameters:**
- `request: GetWarehouseRequest` - запрос получения склада

**Returns:** `Warehouse` - информация о складе

### Справочные данные

#### `async def get_reference_data(data_type: str = "") -> ReferenceDataResponse`
Получить справочные данные.

**Parameters:**
- `data_type: str` - тип данных (опционально)

**Returns:** `ReferenceDataResponse` - справочные данные (стратегии продаж, политики брака, сертификации и т.д.)

#### `async def get_material_types() -> MaterialTypesResponse`
Получить типы материалов.

**Returns:** `MaterialTypesResponse` - список типов материалов

#### `async def get_equipment_types() -> EquipmentTypesResponse`
Получить типы оборудования.

**Returns:** `EquipmentTypesResponse` - список типов оборудования

#### `async def get_workplace_types() -> WorkplaceTypesResponse`
Получить типы рабочих мест.

**Returns:** `WorkplaceTypesResponse` - список типов рабочих мест

#### `async def get_available_defect_policies() -> DefectPoliciesListResponse`
Получить доступные политики работы с браком.

**Returns:** `DefectPoliciesListResponse` - список политик работы с браком

#### `async def get_available_improvements_list() -> ImprovementsListResponse`
Получить список доступных улучшений.

**Returns:** `ImprovementsListResponse` - список доступных улучшений

#### `async def get_available_certifications() -> CertificationsListResponse`
Получить доступные сертификации.

**Returns:** `CertificationsListResponse` - список доступных сертификаций

#### `async def get_available_sales_strategies() -> SalesStrategiesListResponse`
Получить доступные стратегии продаж.

**Returns:** `SalesStrategiesListResponse` - список доступных стратегий продаж

---

## Комбинированные методы

### Комплексная настройка

#### `async def configure_simulation(simulation_id: str, logist_id: Optional[str] = None, supplier_ids: Optional[List[str]] = None, backup_supplier_ids: Optional[List[str]] = None, equipment_assignments: Optional[Dict[str, str]] = None, tender_ids: Optional[List[str]] = None, dealing_with_defects: Optional[str] = None, has_certification: Optional[bool] = None, production_improvements: Optional[List[str]] = None, sales_strategy: Optional[str] = None) -> List[Union[SimulationResponse, Exception]]`
Комплексная настройка симуляции. Выполняет все настройки параллельно.

**Parameters:**
- `simulation_id: str` - ID симуляции
- `logist_id: Optional[str]` - ID логиста
- `supplier_ids: Optional[List[str]]` - список ID основных поставщиков
- `backup_supplier_ids: Optional[List[str]]` - список ID запасных поставщиков
- `equipment_assignments: Optional[Dict[str, str]]` - словарь {workplace_id: equipment_id}
- `tender_ids: Optional[List[str]]` - список ID тендеров
- `dealing_with_defects: Optional[str]` - политика работы с браком
- `has_certification: Optional[bool]` - есть ли сертификация
- `production_improvements: Optional[List[str]]` - список улучшений производства
- `sales_strategy: Optional[str]` - стратегия продаж

**Returns:** `List[Union[SimulationResponse, Exception]]` - результаты всех операций

#### `async def configure_simulation_and_check(...) -> bool`
Комплексная настройка симуляции с проверкой результатов.

**Parameters:** Те же, что и у `configure_simulation`

**Returns:** `bool` - True если все настройки применены успешно

### Полный сценарий

#### `async def run_complete_scenario(config: Optional[Dict[str, Any]] = None) -> SimulationResponse`
Запустить полный сценарий: создание, настройка и запуск симуляции.

**Parameters:**
- `config: Optional[Dict[str, Any]]` - конфигурация симуляции

**Returns:** `SimulationResponse` - полный ответ с результатами

**Пример:**
```python
response = await client.run_complete_scenario({
    "logist_id": "logist-123",
    "supplier_ids": ["supplier-1", "supplier-2"],
    "tender_ids": ["tender-1"]
})
```

#### `async def create_and_configure_simulation(...) -> SimulationConfig`
Создать и настроить симуляцию за один шаг.

**Parameters:** Те же, что и у `configure_simulation` (кроме `simulation_id`)

**Returns:** `SimulationConfig` - конфигурация созданной симуляции

#### `async def create_complete_scenario(config: Optional[Dict[str, Any]] = None) -> SimulationResponse`
Создать, настроить и запустить полный сценарий.

**Parameters:**
- `config: Optional[Dict[str, Any]]` - конфигурация сценария

**Returns:** `SimulationResponse` - полный ответ с результатами

### Получение ресурсов

#### `async def get_available_resources() -> Dict[str, Any]`
Получить все доступные ресурсы параллельно.

**Returns:** `Dict[str, Any]` - словарь со всеми ресурсами:
```python
{
    "suppliers": {"items": [...], "total_count": 10},
    "workers": {"items": [...], "total_count": 5},
    "logists": {"items": [...], "total_count": 3},
    "equipment": {"items": [...], "total_count": 8},
    "tenders": {"items": [...], "total_count": 2},
    "consumers": {"items": [...], "total_count": 4},
    "workplaces": {"items": [...], "total_count": 6}
}
```

#### `async def get_available_resources_simple() -> Dict[str, List]`
Получить все доступные ресурсы параллельно (упрощенная версия).

**Returns:** `Dict[str, List]` - словарь со списками ресурсов:
```python
{
    "suppliers": [...],
    "workers": [...],
    "logists": [...],
    "equipment": [...],
    "tenders": [...],
    "consumers": [...],
    "workplaces": [...]
}
```

---

## Интеграция с FastAPI

### Базовый пример

```python
from fastapi import FastAPI, HTTPException, Depends
from contextlib import asynccontextmanager
from simulation_client import AsyncUnifiedClient
from simulation_client.models import (
    CreateSupplierRequest,
    SimulationConfig,
    SimulationResponse
)

# Глобальный клиент
client: AsyncUnifiedClient = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global client
    client = AsyncUnifiedClient(
        sim_host="localhost",
        sim_port=50051,
        db_host="localhost",
        db_port=50052
    )
    await client.connect()
    yield
    # Shutdown
    await client.close()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health_check():
    """Проверка здоровья сервисов"""
    status = await client.ping()
    if not all(status.values()):
        raise HTTPException(status_code=503, detail="Services unavailable")
    return {"status": "ok", "services": status}

@app.post("/simulations", response_model=SimulationConfig)
async def create_simulation():
    """Создать новую симуляцию"""
    try:
        config = await client.create_simulation()
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/simulations/{simulation_id}", response_model=SimulationResponse)
async def get_simulation(simulation_id: str):
    """Получить информацию о симуляции"""
    try:
        response = await client.get_simulation(simulation_id)
        return response
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/simulations/{simulation_id}/run", response_model=SimulationResponse)
async def run_simulation(simulation_id: str):
    """Запустить симуляцию"""
    try:
        response = await client.run_simulation(simulation_id)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Использование dependency injection

```python
from fastapi import FastAPI, Depends
from typing import Annotated
from simulation_client import AsyncUnifiedClient

async def get_client() -> AsyncUnifiedClient:
    """Dependency для получения клиента"""
    client = AsyncUnifiedClient(
        sim_host="localhost",
        sim_port=50051,
        db_host="localhost",
        db_port=50052
    )
    await client.connect()
    try:
        yield client
    finally:
        await client.close()

app = FastAPI()

@app.get("/suppliers")
async def get_suppliers(client: Annotated[AsyncUnifiedClient, Depends(get_client)]):
    """Получить всех поставщиков"""
    response = await client.get_all_suppliers()
    return response

@app.post("/suppliers")
async def create_supplier(
    request: CreateSupplierRequest,
    client: Annotated[AsyncUnifiedClient, Depends(get_client)]
):
    """Создать нового поставщика"""
    supplier = await client.create_supplier(request)
    return supplier
```

### Полный пример с CRUD операциями

```python
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager
from simulation_client import AsyncUnifiedClient
from simulation_client.models import (
    CreateSupplierRequest,
    UpdateSupplierRequest,
    DeleteSupplierRequest,
    SimulationConfig,
    SimulationResponse,
    GetAllSuppliersResponse,
    Supplier
)

app = FastAPI(title="Simulation API", version="1.0.0")

# Глобальный клиент
client: Optional[AsyncUnifiedClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    client = AsyncUnifiedClient(
        sim_host="localhost",
        sim_port=50051,
        db_host="localhost",
        db_port=50052
    )
    await client.connect()
    yield
    if client:
        await client.close()

app = FastAPI(lifespan=lifespan)

# ==================== Поставщики ====================

@app.get("/api/suppliers", response_model=GetAllSuppliersResponse)
async def get_all_suppliers():
    """Получить всех поставщиков"""
    return await client.get_all_suppliers()

@app.post("/api/suppliers", response_model=Supplier, status_code=status.HTTP_201_CREATED)
async def create_supplier(request: CreateSupplierRequest):
    """Создать нового поставщика"""
    return await client.create_supplier(request)

@app.put("/api/suppliers/{supplier_id}", response_model=Supplier)
async def update_supplier(supplier_id: str, request: UpdateSupplierRequest):
    """Обновить поставщика"""
    request.supplier_id = supplier_id
    return await client.update_supplier(request)

@app.delete("/api/suppliers/{supplier_id}")
async def delete_supplier(supplier_id: str):
    """Удалить поставщика"""
    request = DeleteSupplierRequest(supplier_id=supplier_id)
    result = await client.delete_supplier(request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result

# ==================== Симуляции ====================

@app.post("/api/simulations", response_model=SimulationConfig, status_code=status.HTTP_201_CREATED)
async def create_simulation():
    """Создать новую симуляцию"""
    return await client.create_simulation()

@app.get("/api/simulations/{simulation_id}", response_model=SimulationResponse)
async def get_simulation(simulation_id: str):
    """Получить информацию о симуляции"""
    return await client.get_simulation(simulation_id)

@app.post("/api/simulations/{simulation_id}/run", response_model=SimulationResponse)
async def run_simulation(simulation_id: str):
    """Запустить симуляцию"""
    return await client.run_simulation(simulation_id)

@app.post("/api/simulations/{simulation_id}/configure")
async def configure_simulation(
    simulation_id: str,
    logist_id: Optional[str] = None,
    supplier_ids: Optional[List[str]] = None,
    backup_supplier_ids: Optional[List[str]] = None,
    tender_ids: Optional[List[str]] = None,
    sales_strategy: Optional[str] = None
):
    """Настроить симуляцию"""
    success = await client.configure_simulation_and_check(
        simulation_id=simulation_id,
        logist_id=logist_id,
        supplier_ids=supplier_ids,
        backup_supplier_ids=backup_supplier_ids,
        tender_ids=tender_ids,
        sales_strategy=sales_strategy
    )
    if not success:
        raise HTTPException(status_code=400, detail="Configuration failed")
    return {"success": True, "simulation_id": simulation_id}

# ==================== Метрики ====================

@app.get("/api/simulations/{simulation_id}/metrics/factory")
async def get_factory_metrics(simulation_id: str, step: Optional[int] = None):
    """Получить метрики завода"""
    return await client.get_factory_metrics(simulation_id, step)

@app.get("/api/simulations/{simulation_id}/metrics/production")
async def get_production_metrics(simulation_id: str, step: Optional[int] = None):
    """Получить метрики производства"""
    return await client.get_production_metrics(simulation_id, step)

@app.get("/api/simulations/{simulation_id}/metrics/all")
async def get_all_metrics(simulation_id: str):
    """Получить все метрики"""
    return await client.get_all_metrics(simulation_id)

# ==================== Ресурсы ====================

@app.get("/api/resources")
async def get_all_resources():
    """Получить все доступные ресурсы"""
    return await client.get_available_resources_simple()
```

### Пример с обработкой ошибок

```python
from fastapi import FastAPI, HTTPException
from simulation_client.exceptions import (
    NotFoundError,
    ValidationError,
    ConnectionError,
    TimeoutError
)

app = FastAPI()

@app.post("/api/simulations/{simulation_id}/run")
async def run_simulation(simulation_id: str):
    """Запустить симуляцию с обработкой ошибок"""
    try:
        response = await client.run_simulation(simulation_id)
        return response
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Пример с фоновыми задачами

```python
from fastapi import FastAPI, BackgroundTasks
from simulation_client import AsyncUnifiedClient

app = FastAPI()

async def run_simulation_background(simulation_id: str):
    """Запустить симуляцию в фоне"""
    async with AsyncUnifiedClient() as client:
        await client.run_simulation(simulation_id)

@app.post("/api/simulations/{simulation_id}/run-async")
async def run_simulation_async(simulation_id: str, background_tasks: BackgroundTasks):
    """Запустить симуляцию асинхронно"""
    background_tasks.add_task(run_simulation_background, simulation_id)
    return {"status": "started", "simulation_id": simulation_id}
```

---

## Use Cases

### Use Case 1: Создание и запуск простой симуляции

```python
async def simple_simulation_example():
    """Простой пример создания и запуска симуляции"""
    async with AsyncUnifiedClient() as client:
        # 1. Получаем доступные ресурсы
        suppliers = await client.get_all_suppliers()
        logists = await client.get_all_logists()
        
        # 2. Создаем симуляцию
        config = await client.create_simulation()
        
        # 3. Настраиваем симуляцию
        if logists.logists:
            await client.set_logist(config.simulation_id, logists.logists[0].worker_id)
        
        if suppliers.suppliers:
            await client.add_supplier(config.simulation_id, suppliers.suppliers[0].supplier_id)
        
        # 4. Запускаем симуляцию
        response = await client.run_simulation(config.simulation_id)
        
        # 5. Выводим результаты
        results = response.simulation.results
        print(f"Прибыль: {results.profit:,} ₽")
        print(f"ROI: {results.roi:.2f}%")
        
        return response
```

### Use Case 2: Комплексная настройка симуляции

```python
async def complex_simulation_example():
    """Пример комплексной настройки симуляции"""
    async with AsyncUnifiedClient() as client:
        # 1. Получаем все ресурсы параллельно
        resources = await client.get_available_resources_simple()
        
        # 2. Создаем и настраиваем симуляцию за один шаг
        config = await client.create_and_configure_simulation(
            logist_id=resources["logists"][0].worker_id if resources["logists"] else None,
            supplier_ids=[s.supplier_id for s in resources["suppliers"][:2]],
            backup_supplier_ids=[s.supplier_id for s in resources["suppliers"][2:3]],
            tender_ids=[t.tender_id for t in resources["tenders"][:1]],
            sales_strategy="aggressive",
            has_certification=True
        )
        
        # 3. Запускаем симуляцию
        response = await client.run_simulation(config.simulation_id)
        
        return response
```

### Use Case 3: Пошаговая симуляция с анализом метрик

```python
async def step_by_step_simulation_example():
    """Пример пошаговой симуляции с анализом метрик"""
    async with AsyncUnifiedClient() as client:
        # 1. Создаем и настраиваем симуляцию
        config = await client.create_and_configure_simulation(
            supplier_ids=["supplier-1", "supplier-2"]
        )
        
        # 2. Запускаем несколько шагов
        for step in range(5):
            step_response = await client.run_simulation_step(
                config.simulation_id, 
                step_count=1
            )
            
            # 3. Получаем метрики после каждого шага
            factory_metrics = await client.get_factory_metrics(
                config.simulation_id, 
                step=step_response.simulation.step
            )
            
            print(f"Шаг {step + 1}:")
            print(f"  Прибыльность: {factory_metrics.metrics.profitability:.2f}%")
            print(f"  OEE: {factory_metrics.metrics.oee:.2f}%")
            print(f"  Процент брака: {factory_metrics.metrics.defect_rate:.2f}%")
        
        # 4. Получаем финальные результаты
        final_response = await client.get_simulation(config.simulation_id)
        return final_response
```

### Use Case 4: Сравнение различных конфигураций

```python
async def compare_configurations_example():
    """Пример сравнения различных конфигураций"""
    async with AsyncUnifiedClient() as client:
        configurations = [
            {"sales_strategy": "conservative", "has_certification": False},
            {"sales_strategy": "aggressive", "has_certification": True},
            {"sales_strategy": "balanced", "has_certification": True},
        ]
        
        results = []
        
        for config in configurations:
            # Создаем и настраиваем симуляцию
            sim_config = await client.create_and_configure_simulation(
                sales_strategy=config["sales_strategy"],
                has_certification=config["has_certification"]
            )
            
            # Запускаем симуляцию
            response = await client.run_simulation(sim_config.simulation_id)
            
            # Сохраняем результаты
            results.append({
                "config": config,
                "profit": response.simulation.results.profit,
                "roi": response.simulation.results.roi
            })
        
        # Находим лучшую конфигурацию
        best = max(results, key=lambda x: x["profit"])
        print(f"Лучшая конфигурация: {best['config']}")
        print(f"Прибыль: {best['profit']:,} ₽")
        
        return results
```

### Use Case 5: Мониторинг симуляции в реальном времени

```python
async def real_time_monitoring_example():
    """Пример мониторинга симуляции в реальном времени"""
    async with AsyncUnifiedClient() as client:
        # Создаем симуляцию
        config = await client.create_and_configure_simulation()
        
        # Запускаем симуляцию по шагам
        for step in range(10):
            await client.run_simulation_step(config.simulation_id, step_count=1)
            
            # Получаем все метрики
            all_metrics = await client.get_all_metrics(config.simulation_id)
            
            # Выводим ключевые показатели
            if all_metrics.factory:
                print(f"Шаг {step + 1}:")
                print(f"  Прибыльность: {all_metrics.factory.profitability:.2f}%")
                print(f"  OEE: {all_metrics.factory.oee:.2f}%")
            
            if all_metrics.quality:
                print(f"  Процент брака: {all_metrics.quality.defect_percentage:.2f}%")
            
            if all_metrics.commercial:
                print(f"  Выручка: {all_metrics.commercial.total_receipts:,} ₽")
            
            print("-" * 40)
        
        return await client.get_simulation(config.simulation_id)
```

---

## Обработка ошибок

Библиотека предоставляет специализированные исключения:

- `ConnectionError` - ошибка подключения к сервису
- `TimeoutError` - таймаут операции
- `NotFoundError` - ресурс не найден
- `ValidationError` - ошибка валидации данных
- `AuthenticationError` - ошибка аутентификации
- `ResourceExhaustedError` - исчерпаны ресурсы сервера
- `SimulationError` - общая ошибка симуляции

**Пример обработки:**

```python
from simulation_client.exceptions import (
    NotFoundError,
    ValidationError,
    ConnectionError
)

try:
    response = await client.run_simulation(simulation_id)
except NotFoundError:
    print("Симуляция не найдена")
except ValidationError as e:
    print(f"Ошибка валидации: {e}")
except ConnectionError:
    print("Ошибка подключения к сервису")
```

---

## Модели данных

Все модели данных определены в модуле `simulation_client.models` и основаны на Pydantic. Основные модели:

- `Supplier`, `Worker`, `Logist`, `Equipment`, `Workplace` - базовые сущности
- `Simulation`, `SimulationConfig`, `SimulationResponse` - симуляция
- `SimulationResults` - результаты симуляции
- `FactoryMetrics`, `ProductionMetrics`, `QualityMetrics` и др. - метрики
- `ProductionSchedule`, `WorkshopPlan` - планы производства
- Различные Request/Response модели для API

Подробную информацию о моделях см. в исходном коде модуля `models.py`.

---

## Лицензия

MIT

