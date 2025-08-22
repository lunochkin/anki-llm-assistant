from invoke import task


@task
def test_golden(ctx):
    """Run golden tests with verbose output and showing print statements"""
    ctx.run(f"python -m pytest tests/test_golden.py -v -s")

@task
def cli_query(ctx):
    """Run the CLI with a query"""
    ctx.run(f"python -m src.gen.cli --query 'My decks'")
