"""
Unified service launcher for the Law RAG System.

Starts both the FastAPI backend and the Next.js frontend
concurrently, forwards their output to the terminal with
labeled prefixes, and shuts both down gracefully on Ctrl-C.

Usage:
    python run_service.py                   # dev mode (defaults)
    python run_service.py --mode prod       # prod mode (build + start)
    python run_service.py --api-port 8080 --frontend-port 3001
    python run_service.py --no-frontend     # backend only
    python run_service.py --no-backend      # frontend only

Environment variables (can be set in .env):
    API_HOST            Bind host for the FastAPI server (default: 0.0.0.0)
    API_PORT            Port for the FastAPI server      (default: 8000)
    API_WORKERS         Uvicorn worker count             (default: 1)
    FRONTEND_PORT       Port for the Next.js dev server  (default: 3000)
"""
import argparse
import os
import signal
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from typing import IO, List, Optional

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# ANSI colour codes for log prefixes
# ---------------------------------------------------------------------------
_RESET = "\033[0m"
_BOLD = "\033[1m"
_CYAN = "\033[36m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"


def _colour(text: str, code: str) -> str:
    """Wrap *text* in the given ANSI *code* and reset afterwards."""
    return f"{code}{_BOLD}{text}{_RESET}"


# ---------------------------------------------------------------------------
# Environment loading
# ---------------------------------------------------------------------------

def _load_env() -> None:
    """
    Load variables from the project-root .env file.

    Falls back to the current working directory if the file is not
    found next to this script.
    """
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()


# ---------------------------------------------------------------------------
# Output forwarding
# ---------------------------------------------------------------------------

def _stream_output(stream: IO[bytes], prefix: str, colour: str) -> None:
    """
    Forward every line of *stream* to stdout with a coloured *prefix*.

    Intended to run in a daemon thread so it does not block shutdown.

    Parameters:
        stream  (IO[bytes]): A binary readable stream from subprocess.
        prefix  (str):       Label prepended to every output line.
        colour  (str):       ANSI colour code applied to the prefix.
    """
    label = _colour(f"[{prefix}]", colour)
    try:
        for raw_line in stream:
            try:
                line = raw_line.decode("utf-8", errors="replace").rstrip()
            except Exception:
                line = repr(raw_line)
            print(f"{label} {line}", flush=True)
    except ValueError:
        # Stream was closed (process terminated) — exit the thread quietly.
        pass


# ---------------------------------------------------------------------------
# Process management
# ---------------------------------------------------------------------------

def _start_process(
    cmd: List[str],
    cwd: Optional[str] = None,
    env: Optional[dict] = None,
) -> subprocess.Popen:
    """
    Spawn *cmd* as a subprocess with piped stdout/stderr.

    Parameters:
        cmd  (List[str]):        Command and its arguments.
        cwd  (Optional[str]):    Working directory for the process.
        env  (Optional[dict]):   Environment mapping (inherits os.environ
                                 if None).

    Returns:
        subprocess.Popen: The running subprocess handle.
    """
    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=cwd,
        env=env,
    )


def _attach_streamer(proc: subprocess.Popen, prefix: str, colour: str) -> None:
    """
    Attach a daemon thread that forwards *proc* output to stdout.

    Parameters:
        proc   (subprocess.Popen): Process whose stdout will be streamed.
        prefix (str):              Label for each output line.
        colour (str):              ANSI colour for the label.
    """
    t = threading.Thread(
        target=_stream_output,
        args=(proc.stdout, prefix, colour),
        daemon=True,
    )
    t.start()


def _normalise_backend_url_host(host: str) -> str:
    """
    Convert bind-all hosts into a loopback host for client requests.

    The backend may bind to `0.0.0.0` or `::`, but frontend server-side
    requests must target a routable address such as `127.0.0.1`.

    Parameters:
        host (str): Backend bind host.

    Returns:
        str: Host suitable for HTTP client requests.
    """
    if host in {"0.0.0.0", "::", "[::]", ""}:
        return "127.0.0.1"
    return host


def _prepare_frontend_standalone(frontend_root: str) -> None:
    """
    Copy static assets required by Next.js standalone production output.

    `output: 'standalone'` generates the runtime server in
    `.next/standalone/server.js`, but static assets and the `public`
    directory are not fully embedded there. They must be copied next to
    the standalone server before it is launched, otherwise the frontend
    loads without CSS/JS and appears broken.

    Parameters:
        frontend_root (str): Absolute path to the frontend directory.

    Raises:
        FileNotFoundError: If the standalone build output is missing.
    """
    frontend_path = Path(frontend_root)
    standalone_root = frontend_path / ".next" / "standalone"
    standalone_server = standalone_root / "server.js"

    if not standalone_server.exists():
        raise FileNotFoundError(
            "Missing frontend/.next/standalone/server.js after build"
        )

    static_src = frontend_path / ".next" / "static"
    static_dst = standalone_root / ".next" / "static"
    if static_src.exists():
        static_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(static_src, static_dst, dirs_exist_ok=True)

    public_src = frontend_path / "public"
    public_dst = standalone_root / "public"
    if public_src.exists():
        shutil.copytree(public_src, public_dst, dirs_exist_ok=True)


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed argument values.
    """
    parser = argparse.ArgumentParser(
        description="Law RAG System — start backend + frontend",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=["dev", "prod"],
        default="dev",
        help="Run mode: 'dev' uses hot-reload; 'prod' builds then serves.",
    )
    parser.add_argument(
        "--api-host",
        default=None,
        help=(
            "Override FastAPI bind host. "
            "Falls back to API_HOST env var, then '0.0.0.0'."
        ),
    )
    parser.add_argument(
        "--api-port",
        type=int,
        default=None,
        help=(
            "Override FastAPI port. "
            "Falls back to API_PORT env var, then 8000."
        ),
    )
    parser.add_argument(
        "--api-workers",
        type=int,
        default=None,
        help=(
            "Uvicorn worker count (ignored in dev/reload mode). "
            "Falls back to API_WORKERS env var, then 1."
        ),
    )
    parser.add_argument(
        "--frontend-port",
        type=int,
        default=None,
        help=(
            "Override Next.js port. "
            "Falls back to FRONTEND_PORT env var, then 3000."
        ),
    )
    parser.add_argument(
        "--no-backend",
        action="store_true",
        help="Skip starting the FastAPI backend.",
    )
    parser.add_argument(
        "--no-frontend",
        action="store_true",
        help="Skip starting the Next.js frontend.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Backend / frontend builders
# ---------------------------------------------------------------------------

def _build_backend_cmd(args: argparse.Namespace) -> List[str]:
    """
    Build the command list for starting the FastAPI backend.

    Resolves final values from CLI args > env vars > hard defaults.

    Parameters:
        args (argparse.Namespace): Parsed CLI arguments.

    Returns:
        List[str]: Command and arguments ready for subprocess.
    """
    host = args.api_host or os.environ.get("API_HOST", "0.0.0.0")
    port = args.api_port or int(os.environ.get("API_PORT", "8000"))
    workers = args.api_workers or int(os.environ.get("API_WORKERS", "1"))

    cmd = [
        sys.executable,
        "run_api.py",
        "--host", host,
        "--port", str(port),
        "--workers", str(workers),
    ]
    if args.mode == "dev":
        cmd.append("--reload")
    return cmd


def _build_frontend_cmds(
    args: argparse.Namespace,
) -> List[List[str]]:
    """
    Build the command sequence for starting the Next.js frontend.

    In *prod* mode two sequential commands are returned: build then
    start. In *dev* mode a single command is returned.

    Development uses Webpack explicitly instead of Turbopack. In this
    workspace Turbopack may incorrectly detect the repository root from
    a parent-directory lockfile, which then breaks CSS package
    resolution for `tailwindcss`.

    Parameters:
        args (argparse.Namespace): Parsed CLI arguments.

    Returns:
        List[List[str]]: One or two commands to run (in order).
    """
    port = args.frontend_port or int(
        os.environ.get("FRONTEND_PORT", "3000")
    )

    if args.mode == "dev":
        return [[
            "npm",
            "run",
            "dev",
            "--",
            "--webpack",
            "--port",
            str(port),
        ]]

    # prod: build first, then serve via standalone server.
    # `npm run start` is incompatible with `output: 'standalone'`;
    # the correct entry point is .next/standalone/server.js.
    return [
        ["npm", "run", "build"],
        ["node", ".next/standalone/server.js"],
    ]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Launch backend and/or frontend, stream their output, and wait.

    Registers a SIGINT/SIGTERM handler so both child processes are
    terminated cleanly when the user presses Ctrl-C.
    """
    _load_env()
    args = _parse_args()

    if args.no_backend and args.no_frontend:
        print(
            _colour("ERROR", _RED)
            + " Both --no-backend and --no-frontend are set — nothing to do."
        )
        sys.exit(1)

    project_root = str(Path(__file__).parent)
    frontend_root = str(Path(__file__).parent / "frontend")

    processes: List[subprocess.Popen] = []

    # ------------------------------------------------------------------ #
    # Start backend
    # ------------------------------------------------------------------ #
    if not args.no_backend:
        backend_cmd = _build_backend_cmd(args)
        print(
            _colour("[backend]", _CYAN)
            + f" Starting: {' '.join(backend_cmd)}"
        )
        backend_proc = _start_process(backend_cmd, cwd=project_root)
        _attach_streamer(backend_proc, "backend", _CYAN)
        processes.append(backend_proc)

    # ------------------------------------------------------------------ #
    # Start frontend
    # ------------------------------------------------------------------ #
    if not args.no_frontend:
        frontend_cmds = _build_frontend_cmds(args)

        if args.mode == "prod" and len(frontend_cmds) == 2:
            # Run build synchronously so we don't start the server
            # before the build finishes.
            build_cmd = frontend_cmds[0]
            print(
                _colour("[frontend]", _GREEN)
                + f" Building: {' '.join(build_cmd)}"
            )
            build_env = {**os.environ}
            build_result = subprocess.run(
                build_cmd,
                cwd=frontend_root,
                env=build_env,
            )
            if build_result.returncode != 0:
                print(
                    _colour("[frontend]", _RED)
                    + " Build failed — aborting."
                )
                for p in processes:
                    p.terminate()
                sys.exit(build_result.returncode)

            _prepare_frontend_standalone(frontend_root)
            frontend_cmd = frontend_cmds[1]
        else:
            frontend_cmd = frontend_cmds[0]

        print(
            _colour("[frontend]", _GREEN)
            + f" Starting: {' '.join(frontend_cmd)}"
        )
        frontend_env = {**os.environ}
        # Expose LAW_RAG_API_URL for Next.js server components
        api_host = (
            args.api_host or os.environ.get("API_HOST", "0.0.0.0")
        )
        api_port = args.api_port or int(os.environ.get("API_PORT", "8000"))
        if "LAW_RAG_API_URL" not in frontend_env:
            backend_url_host = _normalise_backend_url_host(api_host)
            frontend_env["LAW_RAG_API_URL"] = (
                f"http://{backend_url_host}:{api_port}"
            )
        # standalone server reads PORT / HOSTNAME from env
        frontend_port = args.frontend_port or int(
            os.environ.get("FRONTEND_PORT", "3000")
        )
        frontend_env.setdefault("PORT", str(frontend_port))
        frontend_env.setdefault("HOSTNAME", "0.0.0.0")
        frontend_proc = _start_process(
            frontend_cmd,
            cwd=frontend_root,
            env=frontend_env,
        )
        _attach_streamer(frontend_proc, "frontend", _GREEN)
        processes.append(frontend_proc)

    # ------------------------------------------------------------------ #
    # Graceful shutdown handler
    # ------------------------------------------------------------------ #
    def _shutdown(signum: int, frame: object) -> None:  # noqa: ARG001
        """Terminate all child processes on SIGINT / SIGTERM."""
        print(
            "\n"
            + _colour("[service]", _YELLOW)
            + " Shutting down…"
        )
        for p in processes:
            if p.poll() is None:
                p.terminate()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # ------------------------------------------------------------------ #
    # Wait for all processes to finish
    # ------------------------------------------------------------------ #
    for p in processes:
        p.wait()

    print(_colour("[service]", _YELLOW) + " All services stopped.")


if __name__ == "__main__":
    main()
