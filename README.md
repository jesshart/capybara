Populates those tedious package versions for your environment.yml.

![swamling](doc/_static/swamling.gif)

# Installation
With `pipx`
```bash
pipx install swaml
```
With `pip`
```bash
python -m pip install swaml
```
# How To Use
Activate the `conda` environment you desire to populate.
```bash
$ conda activate <env>
```
Make sure your `environment.yml` file is in your current working directory. (Currently, it must also be named `environment.yml`.)
```bash
$ ls
... environment.yml ...
```
Run with dry run to be sure of the changes. Otherwise, run without.
```bash
swaml run --dry-run
```