import click
import sys
import logging
from types import SimpleNamespace

from core.deployer import Deployer
from core.config import EXAMPLE_CONFIGS
from core.utils import setup_logging, log_message, stop_all_kubectl_port_forwards


@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose (DEBUG) logging.")
def cli(verbose):
    """
    An interactive one-click deployment script for GenAIExamples.
    """
    setup_logging()
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        log_message("DEBUG", "Verbose mode enabled.")

    app_args = SimpleNamespace(verbose=verbose)

    try:
        # 1. Choose an example
        example_name = click.prompt(
            "Choose an example to manage",
            type=click.Choice(list(EXAMPLE_CONFIGS.keys())),
            default=list(EXAMPLE_CONFIGS.keys())[0],
            show_choices=True
        )
        app_args.example = example_name

        # 2. Choose an action
        action = click.prompt(
            "Choose an action",
            type=click.Choice(["Deploy", "Clear"]),
            default="Deploy",
            show_choices=True
        )
        app_args.action = action

        # 3. Execute
        deployer = Deployer(app_args)

        if action == "Deploy":
            deployer.run_interactive_deployment()
        elif action == "Clear":
            deployer.run_interactive_clear()

    except (ValueError, click.exceptions.Abort) as e:
        log_message("WARN", f"Operation aborted by user or invalid input: {e}")
        sys.exit(1)
    except Exception as e:
        log_message("ERROR", f"An unhandled error occurred: {e}")
        logging.error(e, exc_info=True)
        sys.exit(1)
    finally:
        stop_all_kubectl_port_forwards()
        log_message("INFO", "Script finished.")


if __name__ == '__main__':
    cli()
