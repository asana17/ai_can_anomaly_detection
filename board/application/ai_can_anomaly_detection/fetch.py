"""Download the frames to send.

    python3 -m board.application.ai_can_anomaly_detection.fetch

They are the frames and `injected.json` of the test set `TEST_SET` in the dataset
repository, pinned to a commit. They land in `fetched/` next to this file, under the
path they have in the repository.
"""

from huggingface_hub import hf_hub_download

from board.application.ai_can_anomaly_detection.frames_common import FETCHED, TEST_SET
from common.hub_dirs import download

DATA_REPO = "asana17/ai_can_anomaly_detection_data"
DATA_REVISION = "b5a254a421315c800f5f95dd33b0b62620a4fbc4"


def main():
    download(DATA_REPO, f"{TEST_SET}/frames", FETCHED, repo_type="dataset",
             revision=DATA_REVISION)
    hf_hub_download(DATA_REPO, f"{TEST_SET}/injected.json", repo_type="dataset",
                    revision=DATA_REVISION, local_dir=FETCHED)


if __name__ == "__main__":
    main()
