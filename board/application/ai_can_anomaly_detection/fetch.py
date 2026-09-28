"""Download the frames to send and the model the PC answer is computed with.

    python3 -m board.application.ai_can_anomaly_detection.fetch

They are the attacked test frames of the run `board/lib/deployed_model/` comes from, and
that model as float ONNX. Both are pinned to a commit, so they match the model the
board runs. They land in `fetched/` next to this file.
"""

from pathlib import Path

from common.hub_dirs import download

FETCHED = Path(__file__).resolve().parent / "fetched"
DATA_REPO = "asana17/ai_can_anomaly_detection_data"
DATA_REVISION = "c0e171533acef8f129b1872b4e869dcb7f7221f4"
FRAMES = "frames"
RUNS_REPO = "asana17/ai_can_anomaly_detection_runs"
RUNS_REVISION = "c8bb3b5af97fad6bf55b40cd02056d4bca6a97c0"
MODELS = "quantize/20260916-221145"


def main():
    download(DATA_REPO, FRAMES, FETCHED, repo_type="dataset", revision=DATA_REVISION)
    download(RUNS_REPO, MODELS, FETCHED, revision=RUNS_REVISION)


if __name__ == "__main__":
    main()
