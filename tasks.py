from invoke import task
import os


@task
def test_golden(ctx):
    """Run golden tests with verbose output and showing print statements"""
    ctx.run(f"python -m pytest tests/test_golden.py -v -s")
