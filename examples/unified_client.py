#!/usr/bin/env python3
"""
Пример раздельного использования клиентов.
"""

import asyncio
import logging
from simulation_client import AsyncSimulationClient, AsyncDatabaseClient

from simulation_client.models import SupplierModel


logging.basicConfig(level=logging.INFO)


async def main():
    # Используем разные порты для разных сервисов
    sim_port = 50051  # SimulationService
    db_port = 50052  # DatabaseManager

    print("=== Использование отдельных клиентов ===")

    # Работа с сервисом симуляции
    async with AsyncSimulationClient("localhost", sim_port) as sim_client:
        print(f"Connected to SimulationService on port {sim_port}")

        # Создаем симуляцию
        simulation = await sim_client.create_simulation()
        print(f"Created simulation: {simulation.simulation_id}")

        # Запускаем симуляцию
        results = await sim_client.run_simulation(simulation.simulation_id)
        print(f"Results: profit={results.profit:,}, ROI={results.roi:.1f}%")

    print("\n---")

    # Работа с сервисом базы данных
    async with AsyncDatabaseClient("localhost", db_port) as db_client:
        print(f"Connected to DatabaseManager on port {db_port}")

        # Получаем ресурсы
        suppliers = await db_client.get_all_suppliers()
        workers = await db_client.get_all_workers()
        equipment = await db_client.get_all_equipment()

        print(
            f"Available: {len(suppliers)} suppliers, {len(workers)} workers, {len(equipment)} equipment"
        )

        # Создаем нового поставщика
        new_supplier = await db_client.create_supplier(
            supplier=SupplierModel(
                name="Новый поставщик",
                product_name="Сталь",
                delivery_period=10,
                special_delivery_period=5,
                reliability=0.95,
                product_quality=0.9,
                cost=10000,
                special_delivery_cost=15000,
            )
        )
        print(f"Created supplier: {new_supplier.name}")


if __name__ == "__main__":
    asyncio.run(main())
