"""Board application build inputs and validation."""

from __future__ import annotations

from dataclasses import dataclass
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS = os.path.join(HERE, "application")
LIB = os.path.join(HERE, "lib")
TEST_COMMON = os.path.join(HERE, "test_common")
MODEL = "active_model"
MODEL_FILES = (
    "active_model.c", "active_model.h", "active_model_data.c",
    "active_model_data.h", "active_model_details.h", "model_config.h",
    "threshold.h",
)


@dataclass(frozen=True)
class Application:
    libraries: tuple[str, ...] = ()
    needs_stedgeai: bool = False


APPLICATIONS = {
    "alive": Application(),
    "mbf_test": Application(("mbf",)),
    "rule_check_from_flash": Application(("mbf",)),
    "model_check_from_flash": Application(("mbf", "scale", "model", MODEL), True),
    "ae_reconstruction_from_flash": Application(("scale", "model", MODEL), True),
    "score_and_detect_from_flash": Application(
        ("mbf", "moving", "rules", "scale", "model", "detect", MODEL), True),
}


def application_dir(application):
    given = os.path.abspath(os.path.expanduser(application))
    if os.path.isdir(given):
        return given
    legacy = os.path.join(APPS, application)
    if os.path.isdir(legacy):
        return legacy
    raise SystemExit(f"no application directory {given}")


def application_for(app_dir):
    name = os.path.basename(os.path.normpath(app_dir))
    if name not in APPLICATIONS:
        raise SystemExit(f"no build inputs for application {name}")
    application = APPLICATIONS[name]
    if MODEL in application.libraries:
        model_dir = os.path.join(LIB, MODEL)
        missing = [name for name in MODEL_FILES
                   if not os.path.isfile(os.path.join(model_dir, name))]
        if missing:
            raise SystemExit(f"model input incomplete in {model_dir}: {', '.join(missing)}")
    return application
