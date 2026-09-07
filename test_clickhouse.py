import clickhouse_connect

client = clickhouse_connect.get_client(
    host="vv9y2t9j42.germanywestcentral.azure.clickhouse.cloud",
    port=8443,
    user="default",
    password="X.Q6uuveFLIAk",
    secure=True,
    database="pricing",
)

# Remove incorrect table
client.command("DROP TABLE IF EXISTS products")

# Create exact project schema
client.command("""
CREATE TABLE products
(
    goods_id String,
    product_name String,
    product_url String,

    price Nullable(Float64),
    original_price Nullable(Float64),
    discount Nullable(Float64),

    source String,
    currency String,
    availability String,

    scraped_at String,
    stored_at String
)
ENGINE = MergeTree()
ORDER BY stored_at
""")

print("Exact products table created successfully!")

result = client.query("DESCRIBE TABLE products")

print("\nCloud products schema:")
for row in result.result_rows:
    print(row)

client.close()