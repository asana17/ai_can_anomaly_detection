"""Third-party source trees and runtimes used by board applications."""

from dataclasses import dataclass
import glob
import os
import subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BSP_URL = "https://github.com/tron-forum/mtk3_bsp2.git"
BSP_BASE = "1ab52cc"
UNITY_URL = "https://github.com/ThrowTheSwitch/Unity.git"
UNITY_BASE = "b6763fb"
PATCHES = sorted(glob.glob(os.path.join(HERE, "patches", "*.patch")))
DEFAULT_STEDGEAI = "/Applications/ST/STEdgeAI/4.0"


@dataclass(frozen=True)
class EdgeAIRuntime:
    include_dir: str
    library_dir: str
    library: str


def git(*args):
    subprocess.run(["git", *args], capture_output=True, text=True, check=True)


def add_bsp(project_dir):
    """Clone the patched BSP, or verify an existing clone."""
    bsp = os.path.join(project_dir, "mtk3_bsp2")
    if not os.path.exists(bsp):
        git("clone", BSP_URL, bsp)
        git("-C", bsp, "checkout", BSP_BASE)
        git("-C", bsp, "am", "--keep-cr", *PATCHES)
        done = "cloned"
    else:
        for patch in PATCHES:
            try:
                git("-C", bsp, "apply", "--reverse", "--check", patch)
            except subprocess.CalledProcessError:
                raise SystemExit(f"{bsp} lacks {os.path.basename(patch)}")
        done = "already there"
    git("-C", bsp, "submodule", "update", "--init")
    return done


def add_unity(project_dir):
    """Clone Unity at the pinned revision, or verify an existing clone."""
    unity = os.path.join(project_dir, "Unity")
    if not os.path.exists(unity):
        git("clone", UNITY_URL, unity)
        git("-C", unity, "checkout", UNITY_BASE)
        return "cloned"
    try:
        git("-C", unity, "diff", "--quiet", UNITY_BASE)
    except subprocess.CalledProcessError:
        raise SystemExit(f"{unity} is not at {UNITY_BASE}")
    return "already there"


def stedgeai_runtime(root=None):
    """Locate the v4.0 st-ai headers and Cortex-M33 GCC runtime."""
    root = os.path.abspath(os.path.expanduser(
        root or os.environ.get("STEDGEAI_ROOT", DEFAULT_STEDGEAI)))
    include_dir = os.path.join(root, "Middlewares", "ST", "AI", "Inc")
    library_dir = os.path.join(root, "Middlewares", "ST", "AI", "Lib", "GCC",
                               "ARMCortexM33")
    library = "NetworkRuntime1201_CM33_GCC.a"
    required = (os.path.join(include_dir, "stai.h"), os.path.join(library_dir, library))
    missing = [path for path in required if not os.path.isfile(path)]
    if missing:
        raise SystemExit("ST Edge AI v4.0 st-ai runtime is incomplete: " + ", ".join(missing))
    return EdgeAIRuntime(include_dir, library_dir, library)
