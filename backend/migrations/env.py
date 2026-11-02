from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from alembic import context
from maydrinks import create_app
from maydrinks.models import db
app=create_app()
with app.app_context():
    if context.is_offline_mode():
        context.configure(url=db.engine.url,target_metadata=db.metadata,literal_binds=True,dialect_opts={'paramstyle':'named'})
        with context.begin_transaction(): context.run_migrations()
    else:
        with db.engine.connect() as connection:
            context.configure(connection=connection,target_metadata=db.metadata,compare_type=True)
            with context.begin_transaction(): context.run_migrations()
