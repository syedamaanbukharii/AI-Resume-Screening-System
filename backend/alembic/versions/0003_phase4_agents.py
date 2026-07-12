"""phase4 interview_questions and reports tables

Revision ID: 0003_phase4_agents
Revises: 0002_phase2_pgvector
Create Date: 2026-07-05
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_phase4_agents"
down_revision: str | None = "0002_phase2_pgvector"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create interview_questions and reports tables."""
    op.create_table(
        "interview_questions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "candidate_job_id",
            sa.Uuid(),
            sa.ForeignKey("candidate_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("difficulty", sa.String(10), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("expected_answer", sa.Text(), nullable=True),
        sa.Column("evaluation_criteria", sa.Text(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "category IN ('technical', 'behavioral', 'scenario', 'coding', 'followup')",
            name="ck_iq_category",
        ),
        sa.CheckConstraint(
            "difficulty IN ('easy', 'medium', 'hard')", name="ck_iq_difficulty"
        ),
    )

    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "candidate_job_id",
            sa.Uuid(),
            sa.ForeignKey("candidate_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("strengths", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("weaknesses", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("recommendation", sa.String(30), nullable=True),
        sa.Column("risk_factors", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("interview_plan", sa.Text(), nullable=True),
        sa.Column("model_used", sa.String(50), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "recommendation IN "
            "('strongly_recommend', 'recommend', 'neutral', 'not_recommend')",
            name="ck_report_recommendation",
        ),
    )


def downgrade() -> None:
    """Drop the Phase 4 tables."""
    op.drop_table("reports")
    op.drop_table("interview_questions")
