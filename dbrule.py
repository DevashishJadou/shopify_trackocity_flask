from .connection import db
from sqlalchemy import text

def dup_order_rule(table):
    # SQL command to create a rule
    create_rule_sql = text(f"""
    CREATE OR REPLACE RULE Dup_transaction_{table} AS
        ON INSERT TO {table}
        WHERE EXISTS (
            SELECT 1 FROM {table} WHERE transcation_id = NEW.transcation_id
        )
        DO INSTEAD NOTHING;
    """)

    # Execute the SQL command
    db.session.execute(create_rule_sql)

    # Commit the transaction
    db.session.commit()

    return 200
