import psycopg2

try:
    conn = psycopg2.connect(
        host="fettle-db.cnyyw6yagw6x.ap-south-1.rds.amazonaws.com",
        database="postgres",
        user="postgres",
        password="fettledb",
        port=5432,
        sslmode="require"
    )

    cur = conn.cursor()

    # 🧾 List all tables in the public schema
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema='public'
        ORDER BY table_name;
    """)

    print("📋 Tables in the database:")
    for table in cur.fetchall():
        print("-", table[0])

    table_name = "call_logs"
    cur.execute(f"""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = '{table_name}';
    """)
    print(f"\n🧱 Columns in '{table_name}':")
    for col in cur.fetchall():
        print("-", col[0], ":", col[1])

    table_name = "conversation_turns"
    cur.execute(f"""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = '{table_name}';
    """)

    print(f"\n🧱 Columns in '{table_name}':")
    for col in cur.fetchall():
        print("-", col[0], ":", col[1])

    cur.close()
    conn.close()

except Exception as e:
    print("❌ Database connection failed:", e)

