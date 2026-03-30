from __future__ import annotations

import os
import stat
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = ROOT / "python"

if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

BASE_ENV = os.environ.copy()
BASE_ENV["PYTHONPATH"] = str(PYTHON_DIR)
BASE_ENV["AURORA_SHARE_DIR"] = str(ROOT)


def run_module(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = BASE_ENV.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        [sys.executable, "-m", "aurora", *args],
        cwd=ROOT,
        env=merged_env,
        text=True,
        capture_output=True,
        check=False,
    )


def run_script(script_name: str, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = BASE_ENV.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        [str(ROOT / "bin" / script_name), *args],
        cwd=ROOT,
        env=merged_env,
        text=True,
        capture_output=True,
        check=False,
    )


def write_stub(bin_dir: Path, name: str, body: str) -> None:
    path = bin_dir / name
    normalized_body = body.replace("#!/usr/bin/env bash", "#!/bin/sh", 1)
    path.write_text(normalized_body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def write_os_release(
    root: Path,
    *,
    distro_id: str,
    distro_like: str = "",
    variant_id: str = "",
    name: str = "",
    pretty_name: str = "",
) -> Path:
    path = root / "os-release"
    lines = [f"ID={distro_id}"]
    if distro_like:
        lines.append(f'ID_LIKE="{distro_like}"')
    if variant_id:
        lines.append(f'VARIANT_ID="{variant_id}"')
    if name:
        lines.append(f'NAME="{name}"')
    if pretty_name:
        lines.append(f'PRETTY_NAME="{pretty_name}"')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def setup_host_package_testbed(
    root: Path,
    *,
    family: str,
    distro_id: str,
    distro_like: str,
    repo_packages: tuple[str, ...] = (),
    installed_packages: tuple[str, ...] = (),
    prefer_paru: bool = False,
) -> tuple[dict[str, str], Path]:
    bin_dir = root / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    state_file = root / "installed.txt"
    repo_file = root / "repo.txt"
    state_file.write_text("\n".join(installed_packages) + ("\n" if installed_packages else ""), encoding="utf-8")
    repo_file.write_text("\n".join(repo_packages) + ("\n" if repo_packages else ""), encoding="utf-8")
    write_os_release(root, distro_id=distro_id, distro_like=distro_like, name=distro_id)
    write_stub(bin_dir, "sudo", "#!/bin/sh\nexec \"$@\"\n")

    if family == "arch":
        manager_body = textwrap.dedent(
            f"""\
            #!/bin/sh
            state_file="{state_file}"
            repo_file="{repo_file}"
            target=""
            for arg in "$@"; do
              target="$arg"
            done
            has_state() {{
              /usr/bin/grep -qx "$1" "$state_file"
            }}
            has_repo() {{
              /usr/bin/grep -qx "$1" "$repo_file"
            }}
            remove_state() {{
              tmp="$state_file.tmp"
              /usr/bin/grep -vx "$1" "$state_file" > "$tmp" || true
              /usr/bin/mv "$tmp" "$state_file"
            }}
            case "$1" in
              -Ss)
                if has_repo "$target"; then
                  echo "extra/$target 1.0"
                  exit 0
                fi
                echo "no packages found" >&2
                exit 1
                ;;
              -Q)
                if has_state "$target"; then
                  exit 0
                fi
                exit 1
                ;;
              -S)
                if has_state "$target"; then
                  exit 0
                fi
                if ! has_repo "$target"; then
                  echo "target not found: $target" >&2
                  exit 1
                fi
                echo "$target" >> "$state_file"
                echo "installed $target"
                exit 0
                ;;
              -Rns)
                if ! has_state "$target"; then
                  echo "package not found" >&2
                  exit 1
                fi
                remove_state "$target"
                echo "removed $target"
                exit 0
                ;;
            esac
            exit 1
            """
        )
        write_stub(bin_dir, "pacman", manager_body)
        if prefer_paru:
            write_stub(bin_dir, "paru", manager_body)

    elif family == "debian":
        write_stub(
            bin_dir,
            "apt-cache",
            textwrap.dedent(
                f"""\
                #!/bin/sh
                repo_file="{repo_file}"
                target="$2"
                if grep -qx "$target" "$repo_file"; then
                  echo "$target - pacote de teste"
                  exit 0
                fi
                echo "No packages found" >&2
                exit 1
                """
            ),
        )
        write_stub(
            bin_dir,
            "apt-get",
            textwrap.dedent(
                f"""\
                #!/bin/sh
                state_file="{state_file}"
                repo_file="{repo_file}"
                action="$1"
                target=""
                for arg in "$@"; do
                  target="$arg"
                done
                has_state() {{
                  /usr/bin/grep -qx "$1" "$state_file"
                }}
                has_repo() {{
                  /usr/bin/grep -qx "$1" "$repo_file"
                }}
                remove_state() {{
                  tmp="$state_file.tmp"
                  /usr/bin/grep -vx "$1" "$state_file" > "$tmp" || true
                  /usr/bin/mv "$tmp" "$state_file"
                }}
                case "$action" in
                  install)
                    if has_state "$target"; then
                      exit 0
                    fi
                    if ! has_repo "$target"; then
                      echo "Unable to locate package $target" >&2
                      exit 100
                    fi
                    echo "$target" >> "$state_file"
                    echo "installed $target"
                    exit 0
                    ;;
                  remove)
                    if ! has_state "$target"; then
                      echo "package not installed" >&2
                      exit 1
                    fi
                    remove_state "$target"
                    echo "removed $target"
                    exit 0
                    ;;
                esac
                exit 1
                """
            ),
        )
        write_stub(
            bin_dir,
            "dpkg",
            textwrap.dedent(
                f"""\
                #!/bin/sh
                state_file="{state_file}"
                target="$2"
                if /usr/bin/grep -qx "$target" "$state_file"; then
                  exit 0
                fi
                exit 1
                """
            ),
        )

    elif family == "fedora":
        write_stub(
            bin_dir,
            "dnf",
            textwrap.dedent(
                f"""\
                #!/bin/sh
                state_file="{state_file}"
                repo_file="{repo_file}"
                action="$1"
                target=""
                for arg in "$@"; do
                  target="$arg"
                done
                has_state() {{
                  /usr/bin/grep -qx "$1" "$state_file"
                }}
                has_repo() {{
                  /usr/bin/grep -qx "$1" "$repo_file"
                }}
                remove_state() {{
                  tmp="$state_file.tmp"
                  /usr/bin/grep -vx "$1" "$state_file" > "$tmp" || true
                  /usr/bin/mv "$tmp" "$state_file"
                }}
                case "$action" in
                  search)
                    if has_repo "$target"; then
                      echo "$target.x86_64 : pacote de teste"
                      exit 0
                    fi
                    echo "No matches found" >&2
                    exit 1
                    ;;
                  install)
                    if has_state "$target"; then
                      exit 0
                    fi
                    if ! has_repo "$target"; then
                      echo "No match for argument: $target" >&2
                      exit 1
                    fi
                    echo "$target" >> "$state_file"
                    echo "installed $target"
                    exit 0
                    ;;
                  remove)
                    if ! has_state "$target"; then
                      echo "No match for argument: $target" >&2
                      exit 1
                    fi
                    remove_state "$target"
                    echo "removed $target"
                    exit 0
                    ;;
                esac
                exit 1
                """
            ),
        )
        write_stub(
            bin_dir,
            "rpm",
            textwrap.dedent(
                f"""\
                #!/bin/sh
                state_file="{state_file}"
                target="$2"
                if /usr/bin/grep -qx "$target" "$state_file"; then
                  exit 0
                fi
                exit 1
                """
            ),
        )

    elif family == "opensuse":
        write_stub(
            bin_dir,
            "zypper",
            textwrap.dedent(
                f"""\
                #!/bin/sh
                state_file="{state_file}"
                repo_file="{repo_file}"
                action=""
                target=""
                for arg in "$@"; do
                  case "$arg" in
                    search|install|remove)
                      action="$arg"
                      ;;
                  esac
                  target="$arg"
                done
                has_state() {{
                  /usr/bin/grep -qx "$1" "$state_file"
                }}
                has_repo() {{
                  /usr/bin/grep -qx "$1" "$repo_file"
                }}
                remove_state() {{
                  tmp="$state_file.tmp"
                  /usr/bin/grep -vx "$1" "$state_file" > "$tmp" || true
                  /usr/bin/mv "$tmp" "$state_file"
                }}
                case "$action" in
                  search)
                    if has_repo "$target"; then
                      echo "i | $target | pacote de teste"
                      exit 0
                    fi
                    echo "No matching items found." >&2
                    exit 104
                    ;;
                  install)
                    if has_state "$target"; then
                      exit 0
                    fi
                    if ! has_repo "$target"; then
                      echo "No matching items found." >&2
                      exit 104
                    fi
                    echo "$target" >> "$state_file"
                    echo "installed $target"
                    exit 0
                    ;;
                  remove)
                    if ! has_state "$target"; then
                      echo "package not found" >&2
                      exit 1
                    fi
                    remove_state "$target"
                    echo "removed $target"
                    exit 0
                    ;;
                esac
                exit 1
                """
            ),
        )
        write_stub(
            bin_dir,
            "rpm",
            textwrap.dedent(
                f"""\
                #!/bin/sh
                state_file="{state_file}"
                target="$2"
                if /usr/bin/grep -qx "$target" "$state_file"; then
                  exit 0
                fi
                exit 1
                """
            ),
        )

    env = {
        "PATH": str(bin_dir),
        "AURORA_OS_RELEASE_PATH": str(root / "os-release"),
    }
    return env, state_file
