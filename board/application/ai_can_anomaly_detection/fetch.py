"""Download the frames to send.

    python3 -m board.application.ai_can_anomaly_detection.fetch

They are the attacked test frames in `frames/` of the dataset repository, pinned to a
commit. They land in `fetched/` next to this file.
"""

from board.application.ai_can_anomaly_detection.frames_common import FETCHED
from common.hub_dirs import download

DATA_REPO = "asana17/ai_can_anomaly_detection_data"
DATA_REVISION = "c0e171533acef8f129b1872b4e869dcb7f7221f4"
FRAMES = "frames"


def main():
    download(DATA_REPO, FRAMES, FETCHED, repo_type="dataset", revision=DATA_REVISION)


if __name__ == "__main__":
    main()
