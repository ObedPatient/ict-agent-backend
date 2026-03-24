import os
import django
from dotenv import load_dotenv
import dj_database_url

# Load environment variables
load_dotenv()

# Get database URL
database_url = os.getenv('DATABASE_URL')
print(f"Database URL (hidden password): {database_url.replace(os.getenv('POSTGRES_PASSWORD', ''), '****') if database_url else 'Not set'}")

try:
    # Configure database
    import psycopg2
    
    # Parse the database URL
    conn = dj_database_url.parse(database_url)
    
    # Try to connect
    connection = psycopg2.connect(
        dbname=conn['NAME'],
        user=conn['USER'],
        password=conn['PASSWORD'],
        host=conn['HOST'],
        port=conn['PORT'],
        sslmode='require'
    )
    
    print("✅ Database connection successful!")
    
    # Test query
    cursor = connection.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"PostgreSQL version: {version[0]}")
    
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"❌ Database connection failed: {e}")
