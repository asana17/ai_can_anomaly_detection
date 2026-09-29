# モデルを作る手順

CAN のログから学習用と評価用のデータを作り、モデルを学習して閾値を決め、攻撃を
入れたテストデータで評価するまでの手順。ボードで動かすモデルもここで作る。

## 必要なもの

| もの | 版 |
|---|---|
| Python | 3.9。下の手順で [uv](https://docs.astral.sh/uv/) を使って用意する |
| Hugging Face のアカウント | 書き込みのできるトークン |
| ST Edge AI Core | 4.0.1 と STM32 MCU コンポーネント。ボード用の C コードを作るときだけ使う |

ONNX Runtime 1.19.2 が Python 3.9 に入る最後の版なので、Python は 3.9 にしている。

### Python を用意する

uv を入れる。macOS では Homebrew で、Ubuntu では uv の公式のインストーラで入れる。

```sh
brew install uv                                  # macOS
curl -LsSf https://astral.sh/uv/install.sh | sh  # Ubuntu
```

リポジトリのトップに 3.9 の仮想環境を作り、パッケージを入れる。uv が 3.9 を
ダウンロードするので、OS に入っている Python の版には関係ない。

```sh
uv venv --python 3.9 .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

新しいターミナルでは `source .venv/bin/activate` を実行してから使う。有効な間は
`python3` が 3.9 になり、このガイドとボードのガイドのコマンドはそのまま動く。

## 1. CAN のログを用意する

[Etsin のページ](https://etsin.fairdata.fi/dataset/7586f24f-c91b-41df-92af-283524de8b3e/data)
から `part_1.tar.xz` から `part_4.tar.xz` を `data/` にダウンロードして展開する。
合わせて約 3 GB ある。

```sh
cd data
tar -xJf part_1.tar.xz
tar -xJf part_2.tar.xz
tar -xJf part_3.tar.xz
tar -xJf part_4.tar.xz
```

ログは CC BY 4.0 で公開されている。

## 2. 保存先を用意する

各段階の結果は Hugging Face の 2 つのリポジトリに上がる。データセットはデータ用の
リポジトリに、学習したモデルと評価の結果は結果用のリポジトリに入る。既定は
`asana17/ai_can_anomaly_detection_data` と `asana17/ai_can_anomaly_detection_runs`
で、自分のリポジトリに書くときは 3 の `SETTINGS` で変える。読むだけならログインは
要らない。書くときはログインする。

```sh
hf auth login
```

## 3. 設定ファイルを書く

リポジトリの外に JSON ファイルを 3 つ置く。コードは変えない。このディレクトリの
サンプルを写して書き換えればよい。

| ファイル | 中身 | サンプル |
|---|---|---|
| `SETTINGS` | 既定と違う各段階の設定。すべて既定なら `{}` | [settings.sample.json](settings.sample.json) |
| `MODELS` | 学習する行ごとのモデルと乱数の種 | [models.sample.json](models.sample.json) |
| `WINDOW_MODELS` | 学習する窓のモデル | [window_models.sample.json](window_models.sample.json) |

保存先のリポジトリは `SETTINGS` の `pipeline` に書く。

```json
{"pipeline": {"data_repo": "USER/can_data", "runs_repo": "USER/can_runs"}}
```

各設定の既定と決め方は [common/docs/settings.md](../common/docs/settings.md) にある。

## 4. 実行する

まず何が作られるかを確かめる。各段階が 1 行ずつ、使う既存の結果の日時か、新しく
作るなら `<new>` を出す。このときは何も作らない。

```sh
python3 -m pipeline.worktree SETTINGS MODELS WINDOW_MODELS --dry-run
```

問題なければバックグラウンドで実行する。

```sh
nohup caffeinate -i python3 -m pipeline.worktree SETTINGS MODELS WINDOW_MODELS > LOG 2>&1 &
```

実行されるのは作業ツリーではなく HEAD のコードで、専用の worktree で動く。変更は
コミットしてから実行する。同じ入力から作った結果がリポジトリにある段階は作り直さず、
ダウンロードして使う。既定のリポジトリと設定のままなら、すべての段階がすでにある
ので、ダウンロードだけで終わる。作り直すときは `--rebuild assemble.test_set` のように段階を指定する。

`LOG` の先頭に今回の実行のフォルダが出る。終わったら worktree を消す。

```sh
git worktree remove <snapshot_dir>/<time>/code
```

各段階は [pipeline/README.md](../pipeline/README.md) にある。

## 5. ボード用のモデルを作る

ONNX に書き出したモデルから、ST Edge AI Core で STM32H5 用の C コードを作り、結果用の
リポジトリの `board/<time>` に上げる。

```sh
python3 -m deploy.generate_model_for_board STEDGEAI RUNS_REPO REVISION onnx/<time> out/runs
```

| 引数 | 中身 |
|---|---|
| `STEDGEAI` | ST Edge AI Core のコマンドラインツール `stedgeai`。Ubuntu では `/opt/ST/STEdgeAI/4.0/Utilities/linux/stedgeai` |
| `RUNS_REPO` | 結果用のリポジトリ |
| `REVISION` | ONNX を書き出したときに出た、結果用のリポジトリのコミット |
| `onnx/<time>` | 4 で書き出された ONNX のフォルダ |
| `out/runs` | ダウンロードと出力に使う手元のフォルダ |

作った C コードを `board/lib/` に入れる。どの結果のどのモデルを入れるかは
[board/fetch_model.py](../board/fetch_model.py) の先頭の定数で決まる。

```sh
python3 -m board.fetch_model
```

定数を変えずに実行すると、ボードで動いているモデルがそのまま入る。
