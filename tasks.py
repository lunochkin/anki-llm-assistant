from invoke import task


@task
def test_golden(ctx):
    """Run golden tests with verbose output and showing print statements"""
    ctx.run(f"python -m pytest tests/test_golden.py -v -s")

@task
def cli_query(ctx):
    """Run the CLI with a query"""
    ctx.run(f"python -m src.app.cli --query 'My decks'")

@task
def generate_models(ctx):
    """Generate Pydantic models from YAML schemas"""
    ctx.run("python src/scripts/schema_generator.py")


@task
def generate_tools(ctx):
    """Generate Tier-3 tool files from YAML specifications"""
    ctx.run("python src/scripts/tool_generator.py")

@task
def generate_and_test(ctx):
    """Generate models and tools, then run tests to verify they work"""
    ctx.run("python src/scripts/schema_generator.py")
    ctx.run("python src/scripts/tool_generator.py")
    ctx.run("python -m pytest tests/ -v")
