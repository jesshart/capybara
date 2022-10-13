import json
import logging
import subprocess
import sys
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

log = logging.getLogger("rich")

console = Console()

GREEN_Q = "[bold green]?[/bold green]"
RED_BANG = "[bold red]<!>[/bold red]"
fp = Path("environment.yml")

# Initialize on first run.
if not fp.exists():
    console.print(
        f"{RED_BANG} You must have an {'environment.yml'!r} file present to use capybara."
    )
    sys.exit("Exiting.")

app = typer.Typer()


@app.callback
def callback():
    """ """


@app.command()
def hello():
    print("Hello, World!")


@app.command()
def run(dry_run: bool = False):
    env_json = yaml.load(fp.read_text(), Loader=yaml.Loader)

    dependencies = env_json["dependencies"]
    has_pip = False
    conda_dependencies = []
    pip_dependencies = []

    for d in dependencies:
        if isinstance(d, str):
            conda_dependencies.append(d)
        elif isinstance(d, dict):
            has_pip = True
            log.info("pip packages detected.")
            for pip_d in d["pip"]:
                pip_dependencies.append(pip_d)
        else:
            raise ValueError(f"{d} is not an acceptable type.")

    strip_conda = lambda d: d.split("=")[0]
    strip_pip = lambda d: d.split("=")[0]

    stripped_conda_dependencies = [strip_conda(d) for d in conda_dependencies]
    stripped_pip_dependencies = [strip_pip(d) for d in pip_dependencies]

    stripped_conda_dependencies.sort()
    stripped_pip_dependencies.sort()

    conda_pkg_bytes = subprocess.run(
        ["conda", "list", "--json"], stdout=subprocess.PIPE
    )
    conda_json_raw = conda_pkg_bytes.stdout.decode()
    conda_versions = json.loads(conda_json_raw)

    all_versions = {k["name"] for k in conda_versions}
    missing_conda = set(stripped_conda_dependencies).difference(all_versions)
    missing_pip = set(stripped_pip_dependencies).difference(all_versions)

    MISSING_CONDA = False
    MISSING_PIP = False

    if any(missing_conda):
        MISSING_CONDA = True
        log.warn(f"Missing conda versions for {missing_conda}.")

    if any(missing_pip):
        MISSING_PIP = True
        log.warn(f"Missing conda versions for {missing_pip}.")

    if MISSING_CONDA or MISSING_PIP:
        message = (
            f"Found missing versions which will lead to missing packages"
            f" in your {'environment.yml'!r}. "
            f"You should check your active conda envrionment with `conda list`."
            f"\n\n Continue anyway?"
        )
        typer.confirm(message, abort=True)

    conda_with_versions = []
    pip_with_versions = []
    for dict_ in conda_versions:
        if dict_["name"] in stripped_conda_dependencies:
            string = f"{dict_['name']}={dict_['version']}"
            conda_with_versions.append(string)
        elif dict_["name"] in stripped_pip_dependencies:
            string = f"{dict_['name']}=={dict_['version']}"
            pip_with_versions.append(string)

    # append with the pip dictionary
    package_versions = conda_with_versions.copy()
    package_versions.append({"pip": pip_with_versions})

    env_json.update({"dependencies": package_versions})

    output_yaml = yaml.dump(
        env_json, default_flow_style=False, Dumper=yaml.Dumper
    )

    if dry_run:
        log.info("Running with --dry-run, no changes expected.")
        console.print(output_yaml)
    else:
        fp.write_text(output_yaml)
        console.print(f"Check {fp.name!r} for the change.")

    log.info("Complete!")
