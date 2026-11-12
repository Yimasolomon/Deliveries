
"""link users to customer and driver profiles

Revision ID: 1a2dd96db929
Revises: d4f032aa29f0
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "1a2dd96db929"
down_revision: Union[str, Sequence[str], None] = "d4f032aa29f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("customers") as batch_op:
        batch_op.add_column(
            sa.Column("user_id", sa.Integer(), nullable=True)
        )
        batch_op.create_unique_constraint(
            "uq_customers_user_id",
            ["user_id"],
        )
        batch_op.create_foreign_key(
            "fk_customers_user_id_users",
            "users",
            ["user_id"],
            ["id"],
        )

    with op.batch_alter_table("drivers") as batch_op:
        batch_op.add_column(
            sa.Column("user_id", sa.Integer(), nullable=True)
        )
        batch_op.create_unique_constraint(
            "uq_drivers_user_id",
            ["user_id"],
        )
        batch_op.create_foreign_key(
            "fk_drivers_user_id_users",
            "users",
            ["user_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("drivers") as batch_op:
        batch_op.drop_constraint(
            "fk_drivers_user_id_users",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "uq_drivers_user_id",
            type_="unique",
        )
        batch_op.drop_column("user_id")

    with op.batch_alter_table("customers") as batch_op:
        batch_op.drop_constraint(
            "fk_customers_user_id_users",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "uq_customers_user_id",
            type_="unique",
        )
        batch_op.drop_column("user_id")
