from pricing_engine.database.clickhouse import client

print(client.command("SELECT 1"))