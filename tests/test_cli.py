from click.testing import CliRunner

from cd_ripper.cli import main


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "CD Ripper CLI." in result.output
