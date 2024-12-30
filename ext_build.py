#!/usr/bin/env python3

import os
import shutil
import tempfile
import typing
from os import path as osp
from typing import Any, Literal

import tomli
import tomli_w
from scikit_build_core.build import build_editable, build_sdist, build_wheel


def _rewrite_pyproject(path: str):
    if osp.isdir(path):
        path = osp.join(path, "pyproject.toml")
    with open(path, "rb") as f:
        config = tomli.load(f)

    def read_nested(*keys: str) -> Any:
        cur = config
        for key in keys:
            cur = cur[key]
        return cur

    overwrite = {
        "project": {
            "name": read_nested("tool", "poetry", "name"),
            "version": read_nested("tool", "poetry", "version"),
        },
        "build-system": {
            "build-backend": "scikit_build_core",
        },
    }
    config.update(overwrite)
    # precise overwrite
    if "build-system" in config and "requires" in config["build-system"]:
        r = config["build-system"]["requires"]
        r = list(
            filter(
                lambda x: x
                not in ["cmake", "ninja", "setuptools", "wheel", "poetry-core"],
                r,
            )
        )
        if "scikit-build-core" not in r:
            r.append("scikit-build-core")
        config["build-system"]["requires"] = r

    remove = []

    for key in remove:
        if key in config:
            del config[key]

    with open(path, "wb") as f:
        tomli_w.dump(config, f)


def _build_one(target: Literal["sdist", "wheel", "editable"]) -> str:
    match target:
        case "sdist":
            return build_sdist("dist")
        case "wheel":
            return build_wheel("dist")
        case "editable":
            return build_editable("dist")
        case _:
            raise ValueError(f"Unknown target: {target}")


class ScikitBuild:
    TOOL_NAME = "ScikitBuild"

    def __init__(self):
        super().__init__()
        self._tmp_dir: str | None = None
        self._old_cwd: list[str] = []

    def info(self, text: str):
        print(f"\u001b[34m[{self.TOOL_NAME}]\u001b[0m {text}")

    def _pushd(self, d: str):
        self._old_cwd.append(os.getcwd())
        os.chdir(d)
        self.info(f"Switched to {d}")

    def _popd(self):
        assert len(self._old_cwd) > 0
        d = self._old_cwd.pop()
        os.chdir(d)
        self.info(f"Switched to {d}")

    def _initialize(self):
        self._tmp_dir = tempfile.mkdtemp()
        self.info(f"Using temporary directory: {self._tmp_dir}")

        # sync all source files
        ignore = (
            ".git",
            "__pycache__",
            "*.pyc",
            "venv",
            ".venv",
        )
        for name in os.listdir("."):
            if name == "build":
                continue
            if name in ignore:
                continue
            if osp.isdir(name):
                shutil.copytree(src=name, dst=osp.join(self._tmp_dir, name))
            elif osp.isfile(name):
                shutil.copy(src=name, dst=osp.join(self._tmp_dir, name))
        _rewrite_pyproject(path=self._tmp_dir)

    def _build(self):
        self._pushd(self._tmp_dir)
        # build all
        for target in ["wheel"]:
            _build_one(
                target=typing.cast(Literal["wheel", "sdist", "editable"], target)
            )
        self._popd()

    def _write_results(self):
        # TODO: maybe installing according to cmake manifest is a better idea.
        with open(osp.join(self._tmp_dir, "pyproject.toml"), "rb") as f:
            config = tomli.load(f)
        project_name = config["project"]["name"]
        built_src_dir = osp.join(self._tmp_dir, project_name)
        real_src_dir = osp.abspath(project_name)
        postfixes = [".so", ".dll", ".pyd", ".dylib"]
        for dir_path, dir_names, file_names in os.walk(built_src_dir):
            for file_name in file_names:
                ext = file_name.split(".")[-1]
                if not ext.startswith("."):
                    ext = f".{ext}"
                if ext not in postfixes:
                    continue
                src = osp.join(built_src_dir, file_name)
                dst = osp.join(real_src_dir, file_name)
                shutil.copy(src=src, dst=dst)
                self.info(f"Copied built binary lib: {src} -> {dst}")

    def _cleanup(self):
        if not self._tmp_dir:
            return
        shutil.rmtree(self._tmp_dir)
        self.info(f"Removed temporary directory: {self._tmp_dir}")
        self._tmp_dir = None

    def run(self) -> int:
        self._initialize()
        self._build()
        self._write_results()
        self._cleanup()
        return 0


def main():
    ScikitBuild().run()


if __name__ == "__main__":
    main()
