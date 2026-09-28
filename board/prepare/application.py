"""Board application build inputs and validation."""

from __future__ import annotations

from dataclasses import dataclass
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS = os.path.join(HERE, "application")
LIB = os.path.join(HERE, "lib")
TEST_COMMON = os.path.join(HERE, "test_common")
MODEL = "active_model"          # the model the sample applications check against
DEPLOYED_MODEL = "deployed_model"  # the model the entry runs
DEPLOYED_WINDOW_MODEL = "deployed_window_model"  # the window model the entry runs
MODEL_FILES = (
    "instant_model.c", "instant_model.h", "instant_model_data.c",
    "instant_model_data.h", "instant_model_details.h", "model_config.h",
    "threshold.h",
)


@dataclass(frozen=True)
class Application:
    libraries: tuple[str, ...] = ()
    needs_stedgeai: bool = False
    needs_mbed_crypto: bool = False


APPLICATIONS = {
    "alive": Application(),
    "can_bus_debug": Application(),
    "mbf_test": Application(("mbf",)),
    "test_flash_store": Application(("flash_store",)),
    "rule_check_from_flash": Application(("mbf",)),
    "model_check_from_flash": Application(
        ("mbf", "signals", "scale", "model", "scoring", MODEL), True),
    "ae_reconstruction_from_flash": Application(
        ("signals", "scale", "model", "scoring", MODEL), True),
    "window_model_check_from_flash": Application(
        ("signals", "scale", "model", "scoring", "window_model", DEPLOYED_WINDOW_MODEL,
         MODEL), True),
    "ai_can_anomaly_detection": Application(
        ("mbf", "can_id", "spn_decode", "signal_state", "slots", "frame_ring", "moving",
         "signals", "rules", "scale", "model", "scoring", "detect", "window_model",
         DEPLOYED_WINDOW_MODEL, "alarm_frames_mac", "copy_alarm_frames", "flash_store",
         "store_alarm_frames", "ai_can_anomaly_detection_tasks", "can_sender", "report_can",
         DEPLOYED_MODEL),
        True, True),
    "can_path_from_flash": Application(
        ("mbf", "can_id", "spn_decode", "signal_state", "slots", "frame_ring", "moving",
         "signals", "rules", "scale", "model", "scoring", "detect", "window_model",
         DEPLOYED_WINDOW_MODEL, "alarm_frames_mac", "copy_alarm_frames", "flash_store",
         "store_alarm_frames", "ai_can_anomaly_detection_tasks", "report_uart", MODEL),
        True, True),
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
    for model in (MODEL, DEPLOYED_MODEL):
        if model not in application.libraries:
            continue
        model_dir = os.path.join(LIB, model)
        missing = [name for name in MODEL_FILES
                   if not os.path.isfile(os.path.join(model_dir, name))]
        if missing:
            raise SystemExit(f"model input incomplete in {model_dir}: {', '.join(missing)}")
    return application
