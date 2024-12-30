#!/usr/bin/env python3
import argparse
import os
import shutil
import typing
from os import path as osp
from typing import Any, Literal

import tomli
import tomli_w
from scikit_build_core.build import build_editable, build_sdist, build_wheel


def _rewrite_pyproject(path: str) -> dict[str, Any]:
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

    return config


class ScikitBuild:
    TOOL_NAME = "ScikitBuild"

    def __init__(self):
        super().__init__()
        self._old_cwd: list[str] = []
        self._toml_config: dict[str, Any] = {}
        self._cmake_build_dir = osp.abspath(
            osp.join(osp.dirname(__file__), "build", "cmake-build")
        )
        self._real_source_dir = osp.abspath(os.getcwd())
        self._tmp_dir = osp.join(self._real_source_dir, "build", "src-copy")

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

    def _extra_initialize(self):
        if not osp.exists(self._tmp_dir):
            os.makedirs(self._tmp_dir)
        self.info(f"Using temporary directory: {self._tmp_dir}")

        # sync all source files
        ignore = (
            ".git",
            "__pycache__",
            "*.pyc",
            "venv",
            ".venv",
            "build",
            ".idea",
            ".vscode",
        )
        for name in os.listdir("."):
            if name in ignore:
                continue
            if osp.isdir(name):
                shutil.copytree(
                    src=name, dst=osp.join(self._tmp_dir, name), dirs_exist_ok=True
                )  # overwrite
            elif osp.isfile(name):
                shutil.copy(src=name, dst=osp.join(self._tmp_dir, name))
        self._toml_config = _rewrite_pyproject(path=self._tmp_dir)

    def _build_one(self, target: Literal["sdist", "wheel", "editable"]) -> str:
        py_source_dir = osp.join(
            self._real_source_dir, self._toml_config["project"]["name"]
        )
        settings = {
            "skbuild.build.verbose": True,
            "skbuild.build-dir": self._cmake_build_dir,
            "skbuild.cmake.args": [f"-DCMAKE_INSTALL_PREFIX={py_source_dir}"],
        }
        match target:
            case "sdist":
                return build_sdist("dist", settings)
            case "wheel":
                return build_wheel("dist", settings)
            case "editable":
                return build_editable("dist", settings)
            case _:
                raise ValueError(f"Unknown target: {target}")

    def _build(self):
        self._pushd(self._tmp_dir)
        # build all
        for target in ["wheel"]:
            self._build_one(
                target=typing.cast(Literal["wheel", "sdist", "editable"], target)
            )
        self._popd()

    def clean(self):
        if not osp.exists(self._cmake_build_dir):
            self.info(f"Cannot find cmake build directory: {self._cmake_build_dir}")
            return
        manifest = osp.join(self._cmake_build_dir, "install_manifest.txt")
        if not osp.exists(manifest):
            self.info(f"Cannot find manifest file: {manifest}")
        with open(manifest, "r") as f:
            for target_path in f:
                self.info(f"Removing: {target_path}")
                os.remove(target_path)

    def build(self):
        self._extra_initialize()
        self._build()


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true", default=False)
    return parser.parse_args()


def main():
    args = get_args()
    builder = ScikitBuild()
    if args.clean:
        builder.clean()
    else:
        builder.build()


if __name__ == "__main__":
    main()
