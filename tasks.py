from invoke import task


@task
def test_golden(ctx):
    """Run golden tests with verbose output and showing print statements"""
    ctx.run(f"python -m pytest tests/test_golden.py -v -s")

@task
def cli_help(ctx):
    """Show CLI help"""
    ctx.run("python -m src.app.cli --help")


@task
def cli_chat_help(ctx):
    """Show chat command help"""
    ctx.run("python -m src.app.cli chat --help")


@task
def cli_test_mock(ctx):
    """Run CLI test queries with mock mode"""
    ctx.run("python -m src.app.cli --mode mock test")


@task
def cli_test_anki_connect(ctx):
    """Run CLI test queries with anki_connect mode"""
    ctx.run("python -m src.app.cli --mode anki_connect test")


@task
def cli_test_service_mock(ctx):
    """Test Anki service with mock mode"""
    ctx.run("python -m src.app.cli --mode mock test-service")


@task
def cli_test_service_anki_connect(ctx):
    """Test Anki service with anki_connect mode"""
    ctx.run("python -m src.app.cli --mode anki_connect test-service")


@task
def cli_chat_mock(ctx):
    """Start interactive chat with mock mode"""
    ctx.run("python -m src.app.cli --mode mock chat")


@task
def cli_chat_anki_connect(ctx):
    """Start interactive chat with anki_connect mode"""
    ctx.run("python -m src.app.cli --mode anki_connect chat")

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


@task
def cli_all_tests(ctx):
    """Run all CLI tests (mock and anki_connect modes)"""
    print("Testing CLI with mock mode...")
    ctx.run("python -m src.app.cli --mode mock test")
    print("\n" + "="*50 + "\n")
    print("Testing CLI with anki_connect mode...")
    ctx.run("python -m src.app.cli --mode anki_connect test")


@task
def cli_version(ctx):
    """Show CLI version"""
    ctx.run("python -m src.app.cli --version")


@task
def cli_spec_validate(ctx):
    """Validate that CLI spec can be loaded and parsed"""
    ctx.run("python -c \"from src.app.cli_parser import load_cli_spec, build_parser_from_spec; spec = load_cli_spec(); parser = build_parser_from_spec(spec); print('✅ CLI spec validation successful')\"")
