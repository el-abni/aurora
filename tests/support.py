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
    version_id: str = "",
    variant_id: str = "",
    name: str = "",
    pretty_name: str = "",
) -> Path:
    path = root / "os-release"
    lines = [f"ID={distro_id}"]
    if distro_like:
        lines.append(f'ID_LIKE="{distro_like}"')
    if version_id:
        lines.append(f'VERSION_ID="{version_id}"')
    if variant_id:
        lines.append(f'VARIANT_ID="{variant_id}"')
    if name:
        lines.append(f'NAME="{name}"')
    if pretty_name:
        lines.append(f'PRETTY_NAME="{pretty_name}"')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _aur_helper_stub_body(
    helper_name: str,
    *,
    aur_state_file: Path,
    native_state_file: Path,
    repo_file: Path,
) -> str:
    return textwrap.dedent(
        f"""\
        #!/bin/sh
        helper_name="{helper_name}"
        aur_state_file="{aur_state_file}"
        native_state_file="{native_state_file}"
        repo_file="{repo_file}"
        action="$1"
        target=""
        has_aur_state() {{
          /usr/bin/grep -qx "$1" "$aur_state_file"
        }}
        has_native_state() {{
          /usr/bin/grep -qx "$1" "$native_state_file"
        }}
        has_repo() {{
          /usr/bin/awk -F '\t' -v target="$1" '$1 == target {{ found = 1 }} END {{ exit found ? 0 : 1 }}' "$repo_file"
        }}
        remove_state() {{
          tmp="$aur_state_file.tmp"
          /usr/bin/grep -vx "$1" "$aur_state_file" > "$tmp" || true
          /usr/bin/mv "$tmp" "$aur_state_file"
        }}
        search_key() {{
          printf "%s" "$1" | /usr/bin/tr '[:upper:]' '[:lower:]'
        }}
        for arg in "$@"; do
          case "$arg" in
            -Ss|-S|-Rns|--aur|--needed|--noconfirm|--)
              ;;
            *)
              target="$arg"
              ;;
          esac
        done
        case "$action" in
          -Ss)
            query_key="$(search_key "$target")"
            found=1
            while IFS="$(printf '\\t')" read -r package_name display_label; do
              [ -n "$package_name" ] || continue
              package_key="$(search_key "$package_name")"
              label_key="$(search_key "$display_label")"
              match=1
              case "$package_key" in
                *"$query_key"*) match=0 ;;
              esac
              case "$label_key" in
                *"$query_key"*) match=0 ;;
              esac
              if [ "$match" -eq 0 ]; then
                echo "aur/$package_name 1.0-1"
                echo "    $display_label"
                found=0
              fi
            done < "$repo_file"
            if [ "$found" -eq 0 ]; then
              exit 0
            fi
            echo "no packages found" >&2
            exit 1
            ;;
          -S)
            if has_aur_state "$target"; then
              exit 0
            fi
            if has_native_state "$target"; then
              echo "target already installed from official repos: $target" >&2
              exit 1
            fi
            if ! has_repo "$target"; then
              echo "target not found: $target" >&2
              exit 1
            fi
            echo "$target" >> "$aur_state_file"
            echo "installed $target via $helper_name"
            exit 0
            ;;
          -Rns)
            if ! has_aur_state "$target"; then
              echo "package not found: $target" >&2
              exit 1
            fi
            remove_state "$target"
            echo "removed $target via $helper_name"
            exit 0
            ;;
        esac
        exit 1
        """
    )


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
    normalized_repo_packages: list[tuple[str, str]] = []
    for entry in repo_packages:
        package_name, separator, label_value = entry.partition("|")
        package_name = package_name.strip()
        display_label = label_value.strip() if separator else "pacote de teste"
        normalized_repo_packages.append((package_name, display_label or "pacote de teste"))
    state_file.write_text("\n".join(installed_packages) + ("\n" if installed_packages else ""), encoding="utf-8")
    repo_file.write_text(
        "\n".join(f"{package_name}\t{display_label}" for package_name, display_label in normalized_repo_packages)
        + ("\n" if normalized_repo_packages else ""),
        encoding="utf-8",
    )
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
              /usr/bin/awk -F '\t' -v target="$1" '$1 == target {{ found = 1 }} END {{ exit found ? 0 : 1 }}' "$repo_file"
            }}
            search_key() {{
              printf "%s" "$1" | /usr/bin/tr '[:upper:]' '[:lower:]'
            }}
            repo_label() {{
              /usr/bin/awk -F '\t' -v target="$1" '$1 == target {{ print $2; exit }}' "$repo_file"
            }}
            remove_state() {{
              tmp="$state_file.tmp"
              /usr/bin/grep -vx "$1" "$state_file" > "$tmp" || true
              /usr/bin/mv "$tmp" "$state_file"
            }}
            case "$1" in
              -Ss)
                query_key="$(search_key "$target")"
                found=1
                while IFS="$(printf '\\t')" read -r package_name display_label; do
                  [ -n "$package_name" ] || continue
                  package_key="$(search_key "$package_name")"
                  label_key="$(search_key "$display_label")"
                  match=1
                  case "$package_key" in
                    *"$query_key"*) match=0 ;;
                  esac
                  case "$label_key" in
                    *"$query_key"*) match=0 ;;
                  esac
                  if [ "$match" -eq 0 ]; then
                    echo "extra/$package_name 1.0"
                    echo "    $display_label"
                    found=0
                  fi
                done < "$repo_file"
                if [ "$found" -eq 0 ]; then
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
                query_key="$(printf "%s" "$target" | /usr/bin/tr '[:upper:]' '[:lower:]')"
                found=1
                while IFS="$(printf '\\t')" read -r package_name display_label; do
                  [ -n "$package_name" ] || continue
                  package_key="$(printf "%s" "$package_name" | /usr/bin/tr '[:upper:]' '[:lower:]')"
                  label_key="$(printf "%s" "$display_label" | /usr/bin/tr '[:upper:]' '[:lower:]')"
                  match=1
                  case "$package_key" in
                    *"$query_key"*) match=0 ;;
                  esac
                  case "$label_key" in
                    *"$query_key"*) match=0 ;;
                  esac
                  if [ "$match" -eq 0 ]; then
                    echo "$package_name - $display_label"
                    found=0
                  fi
                done < "$repo_file"
                if [ "$found" -eq 0 ]; then
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
                  /usr/bin/awk -F '\t' -v target="$1" '$1 == target {{ found = 1 }} END {{ exit found ? 0 : 1 }}' "$repo_file"
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
                  /usr/bin/awk -F '\t' -v target="$1" '$1 == target {{ found = 1 }} END {{ exit found ? 0 : 1 }}' "$repo_file"
                }}
                remove_state() {{
                  tmp="$state_file.tmp"
                  /usr/bin/grep -vx "$1" "$state_file" > "$tmp" || true
                  /usr/bin/mv "$tmp" "$state_file"
                }}
                search_key() {{
                  printf "%s" "$1" | /usr/bin/tr '[:upper:]' '[:lower:]'
                }}
                case "$action" in
                  search)
                    query_key="$(search_key "$target")"
                    found=1
                    while IFS="$(printf '\\t')" read -r package_name display_label; do
                      [ -n "$package_name" ] || continue
                      package_key="$(search_key "$package_name")"
                      label_key="$(search_key "$display_label")"
                      match=1
                      case "$package_key" in
                        *"$query_key"*) match=0 ;;
                      esac
                      case "$label_key" in
                        *"$query_key"*) match=0 ;;
                      esac
                      if [ "$match" -eq 0 ]; then
                        echo "$package_name.x86_64 : $display_label"
                        found=0
                      fi
                    done < "$repo_file"
                    if [ "$found" -eq 0 ]; then
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
                  /usr/bin/awk -F '\t' -v target="$1" '$1 == target {{ found = 1 }} END {{ exit found ? 0 : 1 }}' "$repo_file"
                }}
                remove_state() {{
                  tmp="$state_file.tmp"
                  /usr/bin/grep -vx "$1" "$state_file" > "$tmp" || true
                  /usr/bin/mv "$tmp" "$state_file"
                }}
                search_key() {{
                  printf "%s" "$1" | /usr/bin/tr '[:upper:]' '[:lower:]'
                }}
                case "$action" in
                  search)
                    query_key="$(search_key "$target")"
                    found=1
                    while IFS="$(printf '\\t')" read -r package_name display_label; do
                      [ -n "$package_name" ] || continue
                      package_key="$(search_key "$package_name")"
                      label_key="$(search_key "$display_label")"
                      match=1
                      case "$package_key" in
                        *"$query_key"*) match=0 ;;
                      esac
                      case "$label_key" in
                        *"$query_key"*) match=0 ;;
                      esac
                      if [ "$match" -eq 0 ]; then
                        echo "i | $package_name | $display_label"
                        found=0
                      fi
                    done < "$repo_file"
                    if [ "$found" -eq 0 ]; then
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


def setup_aur_testbed(
    root: Path,
    *,
    distro_id: str = "cachyos",
    distro_like: str = "arch",
    repo_packages: tuple[str, ...] = (),
    aur_installed_packages: tuple[str, ...] = (),
    native_installed_packages: tuple[str, ...] = (),
    helpers: tuple[str, ...] = ("paru",),
    name: str = "",
) -> tuple[dict[str, str], Path, Path]:
    bin_dir = root / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    aur_state_file = root / "aur-installed.txt"
    native_state_file = root / "native-installed.txt"
    repo_file = root / "aur-repo.txt"
    normalized_repo_packages: list[tuple[str, str]] = []
    for entry in repo_packages:
        package_name, separator, label_value = entry.partition("|")
        package_name = package_name.strip()
        display_label = label_value.strip() if separator else "pacote AUR de teste"
        normalized_repo_packages.append((package_name, display_label or "pacote AUR de teste"))

    aur_state_file.write_text(
        "\n".join(aur_installed_packages) + ("\n" if aur_installed_packages else ""),
        encoding="utf-8",
    )
    native_state_file.write_text(
        "\n".join(native_installed_packages) + ("\n" if native_installed_packages else ""),
        encoding="utf-8",
    )
    repo_file.write_text(
        "\n".join(f"{package_name}\t{display_label}" for package_name, display_label in normalized_repo_packages)
        + ("\n" if normalized_repo_packages else ""),
        encoding="utf-8",
    )
    write_os_release(root, distro_id=distro_id, distro_like=distro_like, name=name or distro_id)
    write_stub(bin_dir, "sudo", "#!/bin/sh\nexec \"$@\"\n")
    write_stub(
        bin_dir,
        "pacman",
        textwrap.dedent(
            f"""\
            #!/bin/sh
            aur_state_file="{aur_state_file}"
            native_state_file="{native_state_file}"
            action="$1"
            target=""
            for arg in "$@"; do
              case "$arg" in
                -Q|-Qm|-Qn|--)
                  ;;
                *)
                  target="$arg"
                  ;;
              esac
            done
            has_aur_state() {{
              /usr/bin/grep -qx "$1" "$aur_state_file"
            }}
            has_native_state() {{
              /usr/bin/grep -qx "$1" "$native_state_file"
            }}
            print_state() {{
              state_file="$1"
              while IFS= read -r package_name; do
                [ -n "$package_name" ] || continue
                printf "%s %s\\n" "$package_name" "1.0-1"
              done < "$state_file"
            }}
            case "$action" in
              -Qm)
                if [ -n "$target" ]; then
                  if has_aur_state "$target"; then
                    printf "%s %s\\n" "$target" "1.0-1"
                    exit 0
                  fi
                  exit 1
                fi
                print_state "$aur_state_file"
                exit 0
                ;;
              -Qn)
                if [ -n "$target" ]; then
                  if has_native_state "$target"; then
                    printf "%s %s\\n" "$target" "1.0-1"
                    exit 0
                  fi
                  exit 1
                fi
                print_state "$native_state_file"
                exit 0
                ;;
              -Q)
                if has_aur_state "$target" || has_native_state "$target"; then
                  printf "%s %s\\n" "$target" "1.0-1"
                  exit 0
                fi
                exit 1
                ;;
            esac
            exit 1
            """
        ),
    )

    for helper_name in helpers:
        if helper_name in {"paru", "yay"}:
            write_stub(
                bin_dir,
                helper_name,
                _aur_helper_stub_body(
                    helper_name,
                    aur_state_file=aur_state_file,
                    native_state_file=native_state_file,
                    repo_file=repo_file,
                ),
            )
            continue
        write_stub(bin_dir, helper_name, "#!/bin/sh\nexit 0\n")

    env = {
        "PATH": str(bin_dir),
        "AURORA_OS_RELEASE_PATH": str(root / "os-release"),
    }
    return env, aur_state_file, native_state_file


def setup_copr_testbed(
    root: Path,
    *,
    copr_repo: str,
    repo_packages: tuple[str, ...] = (),
    installed_packages: tuple[str, ...] = (),
    installed_package_origins: tuple[str, ...] = (),
    copr_available: bool = True,
    repo_state_observable: bool = True,
    distro_id: str = "fedora",
    distro_like: str = "fedora",
    version_id: str = "42",
    name: str = "Fedora Linux",
) -> tuple[dict[str, str], Path, Path, Path]:
    bin_dir = root / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    state_file = root / "installed.txt"
    repo_file = root / "copr-repo.txt"
    provenance_file = root / "installed-provenance.txt"
    enabled_repo_file = root / "enabled-copr.txt"
    commands_file = root / "commands.txt"
    copr_web_root = root / "copr-web"
    normalized_repo_packages: list[tuple[str, str]] = []
    normalized_installed_origins: list[tuple[str, str]] = []
    for entry in repo_packages:
        package_name, separator, label_value = entry.partition("|")
        package_name = package_name.strip()
        display_label = label_value.strip() if separator else "pacote COPR de teste"
        normalized_repo_packages.append((package_name, display_label or "pacote COPR de teste"))
    for entry in installed_package_origins:
        package_name, separator, from_repo = entry.partition("|")
        package_name = package_name.strip()
        if not package_name:
            continue
        normalized_installed_origins.append((package_name, from_repo.strip()))

    state_file.write_text("\n".join(installed_packages) + ("\n" if installed_packages else ""), encoding="utf-8")
    repo_file.write_text(
        "\n".join(f"{package_name}\t{display_label}" for package_name, display_label in normalized_repo_packages)
        + ("\n" if normalized_repo_packages else ""),
        encoding="utf-8",
    )
    provenance_file.write_text(
        "\n".join(f"{package_name}\t{from_repo}" for package_name, from_repo in normalized_installed_origins)
        + ("\n" if normalized_installed_origins else ""),
        encoding="utf-8",
    )
    enabled_repo_file.write_text("", encoding="utf-8")
    commands_file.write_text("", encoding="utf-8")
    write_os_release(
        root,
        distro_id=distro_id,
        distro_like=distro_like,
        version_id=version_id,
        name=name,
    )
    owner, project = copr_repo.split("/", 1)
    repoid = f"copr:{owner}:{project}"
    repo_slug = f"{owner}-{project}"
    repo_download_dir = copr_web_root / "coprs" / owner / project / "repo" / f"fedora-{version_id}"
    repo_download_dir.mkdir(parents=True, exist_ok=True)
    (repo_download_dir / f"{repo_slug}-fedora-{version_id}.repo").write_text(
        textwrap.dedent(
            f"""\
            [{repoid}]
            name=COPR {copr_repo}
            baseurl=file://{repo_file}
            enabled=1
            gpgcheck=0
            """
        ),
        encoding="utf-8",
    )
    write_stub(bin_dir, "sudo", "#!/bin/sh\nexec \"$@\"\n")
    write_stub(
        bin_dir,
        "dnf",
        textwrap.dedent(
            f"""\
            #!/bin/sh
            state_file="{state_file}"
            repo_file="{repo_file}"
            provenance_file="{provenance_file}"
            enabled_repo_file="{enabled_repo_file}"
            commands_file="{commands_file}"
            requested_repo="{copr_repo}"
            requested_repoid="{repoid}"
            copr_available="{1 if copr_available else 0}"
            repo_state_observable="{1 if repo_state_observable else 0}"
            printf "%s\\n" "$*" >> "$commands_file"
            reposdir=""
            while [ "$#" -gt 0 ]; do
              case "$1" in
                -y)
                  shift
                  ;;
                --disablerepo=*)
                  shift
                  ;;
                --setopt=reposdir=*)
                  reposdir="${{1#--setopt=reposdir=}}"
                  shift
                  ;;
                *)
                  break
                  ;;
              esac
            done
            action="$1"
            target=""
            for arg in "$@"; do
              target="$arg"
            done
            has_state() {{
              /usr/bin/grep -qx "$1" "$state_file"
            }}
            has_repo() {{
              /usr/bin/awk -F '\t' -v target="$1" '$1 == target {{ found = 1 }} END {{ exit found ? 0 : 1 }}' "$repo_file"
            }}
            repo_origin() {{
              /usr/bin/awk -F '\t' -v target="$1" '$1 == target {{ print $2; exit }}' "$provenance_file"
            }}
            repo_enabled() {{
              /usr/bin/grep -qx "$requested_repo" "$enabled_repo_file"
            }}
            repo_file_present() {{
              [ -n "$reposdir" ] && /usr/bin/find "$reposdir" -maxdepth 1 -name '*.repo' -print -quit | /usr/bin/grep -q .
            }}
            search_key() {{
              printf "%s" "$1" | /usr/bin/tr '[:upper:]' '[:lower:]'
            }}
            remove_state() {{
              tmp="$state_file.tmp"
              /usr/bin/grep -vx "$1" "$state_file" > "$tmp" || true
              /usr/bin/mv "$tmp" "$state_file"
            }}
            set_origin() {{
              pkg="$1"
              origin="$2"
              tmp="$provenance_file.tmp"
              if [ -f "$provenance_file" ]; then
                /usr/bin/awk -F '\t' -v target="$pkg" '$1 != target {{ print $0 }}' "$provenance_file" > "$tmp"
              else
                : > "$tmp"
              fi
              printf "%s\t%s\\n" "$pkg" "$origin" >> "$tmp"
              /usr/bin/mv "$tmp" "$provenance_file"
            }}
            remove_origin() {{
              tmp="$provenance_file.tmp"
              if [ -f "$provenance_file" ]; then
                /usr/bin/awk -F '\t' -v target="$1" '$1 != target {{ print $0 }}' "$provenance_file" > "$tmp"
              else
                : > "$tmp"
              fi
              /usr/bin/mv "$tmp" "$provenance_file"
            }}
            case "$action" in
              copr)
                if [ "$copr_available" != "1" ]; then
                  echo "No such command: copr" >&2
                  exit 1
                fi
                case "$2" in
                  --help)
                    echo "usage: dnf copr [enable] owner/project"
                    exit 0
                    ;;
                  enable)
                    repo="$3"
                    printf "%s\\n" "$repo" > "$enabled_repo_file"
                    echo "enabled $repo"
                    exit 0
                    ;;
                  list)
                    if [ "$repo_state_observable" != "1" ]; then
                      echo "failed to list enabled COPR repositories" >&2
                      exit 1
                    fi
                    if [ "$3" = "--enabled" ] && [ -s "$enabled_repo_file" ]; then
                      /usr/bin/cat "$enabled_repo_file"
                    fi
                    exit 0
                    ;;
                esac
                ;;
              repoquery)
                if [ "$2" != "--installed" ]; then
                  exit 1
                fi
                if ! has_state "$target"; then
                  echo "No package matched" >&2
                  exit 1
                fi
                origin="$(repo_origin "$target")"
                printf "%s\t%s\\n" "$target" "$origin"
                exit 0
                ;;
              search)
                if ! repo_file_present; then
                  echo "No matches found." >&2
                  exit 1
                fi
                query_key="$(search_key "$target")"
                found=1
                while IFS="$(printf '\\t')" read -r package_name display_label; do
                  [ -n "$package_name" ] || continue
                  package_key="$(search_key "$package_name")"
                  label_key="$(search_key "$display_label")"
                  match=1
                  case "$package_key" in
                    *"$query_key"*) match=0 ;;
                  esac
                  case "$label_key" in
                    *"$query_key"*) match=0 ;;
                  esac
                  if [ "$match" -eq 0 ]; then
                    echo "$package_name.x86_64 : $display_label"
                    found=0
                  fi
                done < "$repo_file"
                if [ "$found" -eq 0 ]; then
                  exit 0
                fi
                echo "No matches found." >&2
                exit 1
                ;;
              install)
                if has_state "$target"; then
                  exit 0
                fi
                if ! repo_enabled; then
                  echo "No match for argument: $target" >&2
                  exit 1
                fi
                if ! has_repo "$target"; then
                  echo "No match for argument: $target" >&2
                  exit 1
                fi
                echo "$target" >> "$state_file"
                set_origin "$target" "$requested_repoid"
                echo "installed $target"
                exit 0
                ;;
              remove)
                if ! has_state "$target"; then
                  echo "No match for argument: $target" >&2
                  exit 1
                fi
                remove_state "$target"
                remove_origin "$target"
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
        "AURORA_COPR_BASE_URL": copr_web_root.as_uri(),
    }
    return env, state_file, enabled_repo_file, commands_file


def setup_ppa_testbed(
    root: Path,
    *,
    ppa_coordinate: str,
    repo_packages: tuple[str, ...] = (),
    installed_packages: tuple[str, ...] = (),
    add_apt_repository_available: bool = True,
    distro_id: str = "ubuntu",
    distro_like: str = "debian",
    name: str = "Ubuntu",
) -> tuple[dict[str, str], Path, Path, Path]:
    bin_dir = root / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    state_file = root / "installed.txt"
    repo_file = root / "ppa-repo.txt"
    enabled_ppa_file = root / "enabled-ppa.txt"
    indexes_updated_file = root / "apt-indexes-updated.txt"
    commands_file = root / "commands.txt"
    normalized_repo_packages: list[tuple[str, str]] = []
    for entry in repo_packages:
        package_name, separator, label_value = entry.partition("|")
        package_name = package_name.strip()
        display_label = label_value.strip() if separator else "pacote PPA de teste"
        normalized_repo_packages.append((package_name, display_label or "pacote PPA de teste"))

    state_file.write_text("\n".join(installed_packages) + ("\n" if installed_packages else ""), encoding="utf-8")
    repo_file.write_text(
        "\n".join(f"{package_name}\t{display_label}" for package_name, display_label in normalized_repo_packages)
        + ("\n" if normalized_repo_packages else ""),
        encoding="utf-8",
    )
    enabled_ppa_file.write_text("", encoding="utf-8")
    indexes_updated_file.write_text("", encoding="utf-8")
    commands_file.write_text("", encoding="utf-8")
    write_os_release(root, distro_id=distro_id, distro_like=distro_like, name=name)
    write_stub(bin_dir, "sudo", "#!/bin/sh\nexec \"$@\"\n")
    write_stub(
        bin_dir,
        "add-apt-repository",
        textwrap.dedent(
            f"""\
            #!/bin/sh
            commands_file="{commands_file}"
            enabled_ppa_file="{enabled_ppa_file}"
            add_apt_repository_available="{1 if add_apt_repository_available else 0}"
            printf "%s\\n" "$*" >> "$commands_file"
            if [ "$add_apt_repository_available" != "1" ]; then
              echo "add-apt-repository unavailable" >&2
              exit 1
            fi
            if [ "$1" = "--help" ]; then
              echo "usage: add-apt-repository [options] repository"
              exit 0
            fi
            target=""
            for arg in "$@"; do
              case "$arg" in
                -y|-n|--yes|--no-update)
                  ;;
                *)
                  target="$arg"
                  ;;
              esac
            done
            printf "%s\\n" "$target" > "$enabled_ppa_file"
            echo "added $target"
            exit 0
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
            enabled_ppa_file="{enabled_ppa_file}"
            indexes_updated_file="{indexes_updated_file}"
            commands_file="{commands_file}"
            requested_ppa="{ppa_coordinate}"
            printf "%s\\n" "$*" >> "$commands_file"
            action="$1"
            target=""
            for arg in "$@"; do
              target="$arg"
            done
            has_state() {{
              /usr/bin/grep -qx "$1" "$state_file"
            }}
            has_repo() {{
              /usr/bin/awk -F '\t' -v target="$1" '$1 == target {{ found = 1 }} END {{ exit found ? 0 : 1 }}' "$repo_file"
            }}
            ppa_enabled() {{
              /usr/bin/grep -qx "$requested_ppa" "$enabled_ppa_file"
            }}
            remove_state() {{
              tmp="$state_file.tmp"
              /usr/bin/grep -vx "$1" "$state_file" > "$tmp" || true
              /usr/bin/mv "$tmp" "$state_file"
            }}
            case "$action" in
              update)
                if ! ppa_enabled; then
                  echo "PPA not enabled" >&2
                  exit 1
                fi
                printf "ok\\n" > "$indexes_updated_file"
                echo "updated"
                exit 0
                ;;
              install)
                if has_state "$target"; then
                  exit 0
                fi
                if ! ppa_enabled || [ ! -s "$indexes_updated_file" ]; then
                  echo "Unable to locate package $target" >&2
                  exit 100
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

    env = {
        "PATH": str(bin_dir),
        "AURORA_OS_RELEASE_PATH": str(root / "os-release"),
    }
    return env, state_file, enabled_ppa_file, commands_file


def setup_flatpak_testbed(
    root: Path,
    *,
    distro_id: str,
    distro_like: str,
    repo_apps: tuple[str, ...] = (),
    installed_apps: tuple[str, ...] = (),
    remotes: tuple[str, ...] = ("flathub",),
    name: str = "",
) -> tuple[dict[str, str], Path]:
    bin_dir = root / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    state_file = root / "flatpak-installed.txt"
    state_origin_file = root / "flatpak-installed-origin.txt"
    repo_file = root / "flatpak-repo.txt"
    remotes_file = root / "flatpak-remotes.txt"
    normalized_repo_apps: list[tuple[str, str, str]] = []
    repo_origins: dict[str, str] = {}
    for entry in repo_apps:
        parts = [part.strip() for part in entry.split("|")]
        app_id = parts[0] if parts else ""
        display_name = parts[1] if len(parts) >= 2 and parts[1] else app_id
        origin = parts[2] if len(parts) >= 3 and parts[2] else "flathub"
        if not app_id:
            continue
        normalized_repo_apps.append((app_id, display_name or app_id, origin))
        repo_origins.setdefault(app_id, origin)

    normalized_installed_apps: list[tuple[str, str]] = []
    for entry in installed_apps:
        parts = [part.strip() for part in entry.split("|")]
        app_id = parts[0] if parts else ""
        origin = parts[1] if len(parts) >= 2 and parts[1] else repo_origins.get(app_id, "flathub")
        if not app_id:
            continue
        normalized_installed_apps.append((app_id, origin))

    observed_remotes: list[str] = []
    for remote in remotes:
        remote_name = remote.strip()
        if remote_name and remote_name not in observed_remotes:
            observed_remotes.append(remote_name)
    for _app_id, _display_name, origin in normalized_repo_apps:
        if origin not in observed_remotes:
            observed_remotes.append(origin)
    for _app_id, origin in normalized_installed_apps:
        if origin not in observed_remotes:
            observed_remotes.append(origin)

    state_file.write_text(
        "\n".join(app_id for app_id, _origin in normalized_installed_apps)
        + ("\n" if normalized_installed_apps else ""),
        encoding="utf-8",
    )
    state_origin_file.write_text(
        "\n".join(f"{app_id}\t{origin}" for app_id, origin in normalized_installed_apps)
        + ("\n" if normalized_installed_apps else ""),
        encoding="utf-8",
    )
    repo_file.write_text(
        "\n".join(
            f"{app_id}\t{display_name}\t{origin}"
            for app_id, display_name, origin in normalized_repo_apps
        )
        + ("\n" if normalized_repo_apps else ""),
        encoding="utf-8",
    )
    remotes_file.write_text(
        "\n".join(observed_remotes) + ("\n" if observed_remotes else ""),
        encoding="utf-8",
    )
    write_os_release(root, distro_id=distro_id, distro_like=distro_like, name=name or distro_id)
    write_stub(
        bin_dir,
        "flatpak",
        textwrap.dedent(
            f"""\
            #!/bin/sh
            state_file="{state_file}"
            state_origin_file="{state_origin_file}"
            repo_file="{repo_file}"
            remotes_file="{remotes_file}"
            action="$1"
            target=""
            remote=""
            columns="application,name,version,branch,remotes"
            has_state() {{
              /usr/bin/grep -qx "$1" "$state_file"
            }}
            has_remote() {{
              /usr/bin/grep -qx "$1" "$remotes_file"
            }}
            has_repo() {{
              /usr/bin/awk -F '\t' -v target="$1" '$1 == target {{ found = 1 }} END {{ exit found ? 0 : 1 }}' "$repo_file"
            }}
            has_repo_in_remote() {{
              /usr/bin/awk -F '\t' -v target="$1" -v remote="$2" '$1 == target && $3 == remote {{ found = 1 }} END {{ exit found ? 0 : 1 }}' "$repo_file"
            }}
            remove_state() {{
              tmp="$state_file.tmp"
              /usr/bin/grep -vx "$1" "$state_file" > "$tmp" || true
              /usr/bin/mv "$tmp" "$state_file"
            }}
            remove_state_origin() {{
              tmp="$state_origin_file.tmp"
              /usr/bin/grep -v "^$1\t" "$state_origin_file" > "$tmp" || true
              /usr/bin/mv "$tmp" "$state_origin_file"
            }}
            search_key() {{
              printf "%s" "$1" | /usr/bin/tr '[:upper:]' '[:lower:]'
            }}
            repo_name() {{
              /usr/bin/awk -F '\t' -v target="$1" -v remote="$2" '$1 == target && (!remote || $3 == remote) {{ print $2; exit }}' "$repo_file"
            }}
            state_origin() {{
              /usr/bin/awk -F '\t' -v target="$1" '$1 == target {{ print $2; exit }}' "$state_origin_file"
            }}
            print_remote_row() {{
              app_id="$1"
              app_name="$2"
              app_origin="$3"
              case "$columns" in
                application,name|application,name,origin)
                  if [ "$columns" = "application,name,origin" ]; then
                    printf "%s\\t%s\\t%s\\n" "$app_id" "$app_name" "$app_origin"
                  else
                    printf "%s\\t%s\\n" "$app_id" "$app_name"
                  fi
                  ;;
                name)
                  printf "%s\\n" "$app_name"
                  ;;
                application)
                  printf "%s\\n" "$app_id"
                  ;;
                origin)
                  printf "%s\\n" "$app_origin"
                  ;;
                application,name,version,branch,origin)
                  printf "%s\\t%s\\t%s\\t%s\\t%s\\n" "$app_id" "$app_name" "1.0" "stable" "$app_origin"
                  ;;
                application,name,version,branch,remotes)
                  printf "%s\\t%s\\t%s\\t%s\\t%s\\n" "$app_id" "$app_name" "1.0" "stable" "$app_origin"
                  ;;
                application,name,version,branch)
                  printf "%s\\t%s\\t%s\\t%s\\n" "$app_id" "$app_name" "1.0" "stable"
                  ;;
                *)
                  printf "%s\\t%s\\t%s\\t%s\\t%s\\n" "$app_id" "$app_name" "1.0" "stable" "$app_origin"
                  ;;
              esac
            }}
            print_list_row() {{
              app_id="$1"
              app_name="$2"
              app_origin="$3"
              case "$columns" in
                application,name)
                  printf "%s\\t%s\\n" "$app_id" "$app_name"
                  ;;
                application,name,origin)
                  printf "%s\\t%s\\t%s\\n" "$app_id" "$app_name" "$app_origin"
                  ;;
                *)
                  printf "%s\\t%s\\n" "$app_id" "$app_name"
                  ;;
              esac
            }}
            for arg in "$@"; do
              case "$arg" in
                search|remote-ls|remotes|info|list|install|uninstall|--show-ref|--user|--system|--noninteractive|-y|--app)
                  ;;
                --columns=*)
                  columns="${{arg#--columns=}}"
                  ;;
                *)
                  if [ "$action" = "remote-ls" ] && [ -z "$remote" ]; then
                    remote="$arg"
                  elif [ "$action" = "install" ] && [ -z "$remote" ]; then
                    remote="$arg"
                  else
                    target="$arg"
                  fi
                  ;;
              esac
            done
            case "$action" in
              remotes)
                while IFS= read -r remote_name; do
                  [ -n "$remote_name" ] || continue
                  case "$columns" in
                    name|*)
                      printf "%s\\n" "$remote_name"
                      ;;
                  esac
                done < "$remotes_file"
                exit 0
                ;;
              remote-ls)
                if ! has_remote "$remote"; then
                  echo "error: Remote '$remote' not found" >&2
                  exit 1
                fi
                while IFS="$(printf '\\t')" read -r app_id app_name app_origin; do
                  [ -n "$app_id" ] || continue
                  [ "$app_origin" = "$remote" ] || continue
                  print_remote_row "$app_id" "$app_name" "$app_origin"
                done < "$repo_file"
                exit 0
                ;;
              search)
                query_key="$(search_key "$target")"
                found=1
                while IFS="$(printf '\\t')" read -r app_id app_name app_origin; do
                  [ -n "$app_id" ] || continue
                  app_key="$(search_key "$app_id")"
                  name_key="$(search_key "$app_name")"
                  match=1
                  case "$app_key" in
                    *"$query_key"*) match=0 ;;
                  esac
                  case "$name_key" in
                    *"$query_key"*) match=0 ;;
                  esac
                  if [ "$match" -eq 0 ]; then
                    print_remote_row "$app_id" "$app_name" "$app_origin"
                    found=0
                  fi
                done < "$repo_file"
                if [ "$found" -eq 0 ]; then
                  exit 0
                fi
                echo "No matches found" >&2
                exit 1
                ;;
              info)
                if has_state "$target"; then
                  echo "app/$target/x86_64/stable"
                  exit 0
                fi
                echo "error: $target/*unspecified*/*unspecified* not installed" >&2
                exit 1
                ;;
              list)
                while IFS= read -r app_id; do
                  [ -n "$app_id" ] || continue
                  app_origin="$(state_origin "$app_id")"
                  app_name="$(repo_name "$app_id" "$app_origin")"
                  if [ -z "$app_name" ]; then
                    app_name="$app_id"
                  fi
                  print_list_row "$app_id" "$app_name" "$app_origin"
                done < "$state_file"
                exit 0
                ;;
              install)
                if has_state "$target"; then
                  exit 0
                fi
                if ! has_remote "$remote" || ! has_repo_in_remote "$target" "$remote"; then
                  echo "error: No remote refs found for '$target'" >&2
                  exit 1
                fi
                echo "$target" >> "$state_file"
                printf "%s\\t%s\\n" "$target" "$remote" >> "$state_origin_file"
                echo "installed $target"
                exit 0
                ;;
              uninstall)
                if ! has_state "$target"; then
                  echo "error: No installed refs found for '$target'" >&2
                  exit 1
                fi
                remove_state "$target"
                remove_state_origin "$target"
                echo "uninstalled $target"
                exit 0
                ;;
            esac
            exit 1
            """
        ),
    )
    return (
        {
            "PATH": str(bin_dir),
            "AURORA_OS_RELEASE_PATH": str(root / "os-release"),
        },
        state_file,
    )


def _write_toolbox_container_backend_stubs(
    bin_dir: Path,
    *,
    family: str,
    state_file: Path,
    repo_file: Path,
    include_sudo: bool = True,
) -> None:
    if include_sudo:
        write_stub(bin_dir, "sudo", "#!/bin/sh\nexec \"$@\"\n")
    write_stub(
        bin_dir,
        "cat",
        textwrap.dedent(
            """\
            #!/bin/sh
            if [ "$1" = "/etc/os-release" ] && [ -n "$TOOLBOX_CONTAINER_ROOT" ]; then
              exec /bin/cat "$TOOLBOX_CONTAINER_ROOT/os-release"
            fi
            exec /bin/cat "$@"
            """
        ),
    )

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
              /usr/bin/awk -F '\t' -v target="$1" '$1 == target {{ found = 1 }} END {{ exit found ? 0 : 1 }}' "$repo_file"
            }}
            search_key() {{
              printf "%s" "$1" | /usr/bin/tr '[:upper:]' '[:lower:]'
            }}
            remove_state() {{
              tmp="$state_file.tmp"
              /usr/bin/grep -vx "$1" "$state_file" > "$tmp" || true
              /usr/bin/mv "$tmp" "$state_file"
            }}
            case "$1" in
              -Ss)
                query_key="$(search_key "$target")"
                found=1
                while IFS="$(printf '\\t')" read -r package_name display_label; do
                  [ -n "$package_name" ] || continue
                  package_key="$(search_key "$package_name")"
                  label_key="$(search_key "$display_label")"
                  match=1
                  case "$package_key" in
                    *"$query_key"*) match=0 ;;
                  esac
                  case "$label_key" in
                    *"$query_key"*) match=0 ;;
                  esac
                  if [ "$match" -eq 0 ]; then
                    echo "extra/$package_name 1.0"
                    echo "    $display_label"
                    found=0
                  fi
                done < "$repo_file"
                if [ "$found" -eq 0 ]; then
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
        return

    if family == "debian":
        write_stub(
            bin_dir,
            "apt-cache",
            textwrap.dedent(
                f"""\
                #!/bin/sh
                repo_file="{repo_file}"
                target="$2"
                query_key="$(printf "%s" "$target" | /usr/bin/tr '[:upper:]' '[:lower:]')"
                found=1
                while IFS="$(printf '\\t')" read -r package_name display_label; do
                  [ -n "$package_name" ] || continue
                  package_key="$(printf "%s" "$package_name" | /usr/bin/tr '[:upper:]' '[:lower:]')"
                  label_key="$(printf "%s" "$display_label" | /usr/bin/tr '[:upper:]' '[:lower:]')"
                  match=1
                  case "$package_key" in
                    *"$query_key"*) match=0 ;;
                  esac
                  case "$label_key" in
                    *"$query_key"*) match=0 ;;
                  esac
                  if [ "$match" -eq 0 ]; then
                    echo "$package_name - $display_label"
                    found=0
                  fi
                done < "$repo_file"
                if [ "$found" -eq 0 ]; then
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
                  /usr/bin/awk -F '\t' -v target="$1" '$1 == target {{ found = 1 }} END {{ exit found ? 0 : 1 }}' "$repo_file"
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
        return

    if family == "fedora":
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
                  /usr/bin/awk -F '\t' -v target="$1" '$1 == target {{ found = 1 }} END {{ exit found ? 0 : 1 }}' "$repo_file"
                }}
                remove_state() {{
                  tmp="$state_file.tmp"
                  /usr/bin/grep -vx "$1" "$state_file" > "$tmp" || true
                  /usr/bin/mv "$tmp" "$state_file"
                }}
                search_key() {{
                  printf "%s" "$1" | /usr/bin/tr '[:upper:]' '[:lower:]'
                }}
                case "$action" in
                  search)
                    query_key="$(search_key "$target")"
                    found=1
                    while IFS="$(printf '\\t')" read -r package_name display_label; do
                      [ -n "$package_name" ] || continue
                      package_key="$(search_key "$package_name")"
                      label_key="$(search_key "$display_label")"
                      match=1
                      case "$package_key" in
                        *"$query_key"*) match=0 ;;
                      esac
                      case "$label_key" in
                        *"$query_key"*) match=0 ;;
                      esac
                      if [ "$match" -eq 0 ]; then
                        echo "$package_name.x86_64 : $display_label"
                        found=0
                      fi
                    done < "$repo_file"
                    if [ "$found" -eq 0 ]; then
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
        return

    if family == "opensuse":
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
                  /usr/bin/awk -F '\t' -v target="$1" '$1 == target {{ found = 1 }} END {{ exit found ? 0 : 1 }}' "$repo_file"
                }}
                remove_state() {{
                  tmp="$state_file.tmp"
                  /usr/bin/grep -vx "$1" "$state_file" > "$tmp" || true
                  /usr/bin/mv "$tmp" "$state_file"
                }}
                search_key() {{
                  printf "%s" "$1" | /usr/bin/tr '[:upper:]' '[:lower:]'
                }}
                case "$action" in
                  search)
                    query_key="$(search_key "$target")"
                    found=1
                    while IFS="$(printf '\\t')" read -r package_name display_label; do
                      [ -n "$package_name" ] || continue
                      package_key="$(search_key "$package_name")"
                      label_key="$(search_key "$display_label")"
                      match=1
                      case "$package_key" in
                        *"$query_key"*) match=0 ;;
                      esac
                      case "$label_key" in
                        *"$query_key"*) match=0 ;;
                      esac
                      if [ "$match" -eq 0 ]; then
                        echo "i | $package_name | $display_label"
                        found=0
                      fi
                    done < "$repo_file"
                    if [ "$found" -eq 0 ]; then
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


def setup_toolbox_testbed(
    root: Path,
    *,
    host_distro_id: str,
    host_distro_like: str,
    toolboxes: tuple[dict[str, object], ...],
    host_name: str = "",
) -> tuple[dict[str, str], dict[str, Path]]:
    bin_dir = root / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    toolboxes_root = root / "toolboxes"
    toolboxes_root.mkdir(parents=True, exist_ok=True)
    state_files: dict[str, Path] = {}

    for spec in toolboxes:
        toolbox_name = str(spec["name"])
        family = str(spec["family"])
        distro_id = str(spec.get("distro_id", family))
        distro_like = str(spec.get("distro_like", family))
        repo_packages = tuple(spec.get("repo_packages", ()))
        installed_packages = tuple(spec.get("installed_packages", ()))
        include_sudo = bool(spec.get("include_sudo", True))
        display_name = str(spec.get("display_name", distro_id))

        container_root = toolboxes_root / toolbox_name
        container_bin = container_root / "bin"
        container_bin.mkdir(parents=True, exist_ok=True)
        state_file = container_root / "installed.txt"
        repo_file = container_root / "repo.txt"
        normalized_repo_packages: list[tuple[str, str]] = []
        for entry in repo_packages:
            package_name, separator, label_value = str(entry).partition("|")
            package_name = package_name.strip()
            display_label = label_value.strip() if separator else "pacote de teste"
            if package_name:
                normalized_repo_packages.append((package_name, display_label or "pacote de teste"))
        state_file.write_text(
            "\n".join(str(item) for item in installed_packages) + ("\n" if installed_packages else ""),
            encoding="utf-8",
        )
        repo_file.write_text(
            "\n".join(
                f"{package_name}\t{display_label}"
                for package_name, display_label in normalized_repo_packages
            )
            + ("\n" if normalized_repo_packages else ""),
            encoding="utf-8",
        )
        write_os_release(
            container_root,
            distro_id=distro_id,
            distro_like=distro_like,
            name=display_name,
        )
        _write_toolbox_container_backend_stubs(
            container_bin,
            family=family,
            state_file=state_file,
            repo_file=repo_file,
            include_sudo=include_sudo,
        )
        state_files[toolbox_name] = state_file

    write_os_release(root, distro_id=host_distro_id, distro_like=host_distro_like, name=host_name or host_distro_id)
    write_stub(
        bin_dir,
        "toolbox",
        textwrap.dedent(
            f"""\
            #!/bin/sh
            toolboxes_root="{toolboxes_root}"
            if [ "$1" = "list" ] && [ "$2" = "--containers" ]; then
              echo "CONTAINER ID  CONTAINER NAME    CREATED       STATUS   IMAGE NAME"
              index=1
              for container_dir in "$toolboxes_root"/*; do
                [ -d "$container_dir" ] || continue
                container_name="${{container_dir##*/}}"
                printf "%012x  %s  2 hours ago  running  quay.io/fedora/fedora-toolbox:41\\n" "$index" "$container_name"
                index=$((index + 1))
              done
              exit 0
            fi
            if [ "$1" = "run" ] && [ "$2" = "--container" ]; then
              container_name="$3"
              container_root="$toolboxes_root/$container_name"
              shift 3
              if [ "$1" = "--" ]; then
                shift
              fi
              if [ ! -d "$container_root" ]; then
                echo "container not found: $container_name" >&2
                exit 1
              fi
              export TOOLBOX_CONTAINER_ROOT="$container_root"
              export PATH="$container_root/bin"
              if [ "$1" = "sh" ]; then
                shift
                exec /bin/sh "$@"
              fi
              exec "$@"
            fi
            echo "unsupported toolbox invocation" >&2
            exit 1
            """
        ),
    )

    return (
        {
            "PATH": str(bin_dir),
            "AURORA_OS_RELEASE_PATH": str(root / "os-release"),
        },
        state_files,
    )
