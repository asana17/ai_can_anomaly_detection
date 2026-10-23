# メインのデモをCubeIDE だけで動かす

[ai_can_anomaly_detection](ai_can_anomaly_detection) は、メインのデモ
`ai_can_anomaly_detection` をビルドできる状態にした STM32CubeIDE のプロジェクトである。

配線と USB-CAN アダプタは [ボードの手順](../guidelines/board_guide_ja.md) の 2 と 3 のとおりにつなぐ。

## 1. リポジトリを取ってくる

mtk3_bsp2 を含めるため、`--recursive` を付けてcloneする。

```sh
git clone --recursive https://github.com/asana17/ai_can_anomaly_detection.git
```

## 2. CubeIDE に読み込む

CubeIDE を起動すると workspace を聞かれる。リポジトリの外のフォルダならどこでもよく、
初めに出る `~/STM32CubeIDE/workspace_2.1.1` のままでよい。workspace には CubeIDE の設定だけが入り、
プロジェクトのファイルはリポジトリに置いたまま使う。

File、Import、General、Existing Projects into Workspace を選ぶ。ルートには
`cubeide/ai_can_anomaly_detection` を選ぶ。Copy projects into workspace のチェックは外す。

ビルドできることを確かめる。

1. Project Explorer で `ai_can_anomaly_detection` を選ぶ。
2. Project、Build Configurations、Set Active で Release を選ぶ。4 の書き込みも Release でビルドする。
3. Project、Build Project を選ぶ。コンソールの最後に `Build Finished. 0 errors` が出る。

ボードに書き込めることを確かめる。バンク 2 は消さない。

1. Run、Run Configurations を開く。
2. 左の一覧の STM32 C/C++ Application の下にある `ai_can_anomaly_detection` を選び、右下の Run を押す。
3. コンソールの最後に `Download verified successfully` が出る。

## 3. SWAP_BANK を確かめる

Run、External Tools、External Tools Configurations を開く。左の一覧の Program の下にある
`show_option_bytes` を選び、右下の Run を押す。

コンソールに出る `SWAP_BANK` が 0 であることを確かめる。1 のときはバンクが入れ替わっているため直す。

## 4. バンク 2 を消して書き込む

Run、Run Configurations を開く。左の一覧の Launch Group の下にある `erase_bank_2_and_run`
を選び、右下の Run を押す。
これにより最初にバンク 2 を消してボードをリセットし、次にビルドして書き込む。

コンソールの最後に`Download verified successfully` が出れば完了。

ボードは起動するとバンク 2 に残っているものを警報の記録として読むので、前のデータを先に消している。

## 5. UART を見る

1. Console タブを開く。見当たらないときは Window、Show View、Console で出す。
2. Console ビューの右上にある Open Console（モニタに「+」が付いたアイコン）の ▼ を押し、
   Command Shell Console を選ぶ。
3. 開いたダイアログで Connection Type を Serial Port にし、Connection name の横の New... を押す。
4. 名前は任意で付ける。Serial port は `/dev/cu.usbmodem` で始まるもの（Ubuntu では
   `/dev/ttyACM0`）、Baud rate は 115200 にする。Finish を押し、OK で閉じる。
5. ボードの黒いボタン（RESET、B2）を押す。`reading FDCAN1` は起動したときに 1 回だけ出るので、
   開く前に出たものは見えない。

`reading FDCAN1` が出れば受信を始めている。

## 6. フレームを送る

ここからの起動設定は、3 と同じく External Tools Configurations の Program の下から選んで
Run を押す。どれもリポジトリのトップで PC 側の Python を動かす。

### 6.1 Python を用意する

最初に一度だけ `setup_python` を実行する。uv が無ければ入れ、`.venv` を作って
`requirements.txt` のパッケージを入れる。macOS では Homebrew で libusb も入れるので、
Homebrew が入っている必要がある。終わるまで数分かかる。

### 6.2 PC で同じモデルを動かす

`expected_both_alarms` を実行する。警報が始まる行と終わる行が出る。読み方は
[ボードの手順の 7.1.2](../guidelines/board_guide_ja.md#712-pc-で同じモデルを動かす) にある。

### 6.3 ボードにフレームを送る

`send_both_alarms` を実行する。USB-CAN アダプタからログのフレームを送り、ボードが CAN に
送った警報を中身に直してコンソールに出す。約 1 分で終わる。

途中でコンソールの停止ボタンを押すと、アダプタが閉じないまま止まる。そのときは USB-CAN
アダプタを USB から抜いて挿し直してから、もう一度送る。最後の行の `echoed` が 0 のときも
アダプタが何も読めていないので、同じく抜いて挿し直してから送り直す。

コンソールには警報の始まりと終わり、Flash への保存の行だけが出る。全部の行は
`received_frames.txt` に残る。2026-10-23 に動かしたときは次のように出た。

```
sending 50001 frames from 1792744433.341
row 6704: window alarm start, 90 ms after the row was made
row 6704: window alarm frames stored, 178 ms after the window alarm start, 2019 frames
row 6713: alarm start, 0 ms after the row was made
row 6713: alarm frames stored, 175 ms after the alarm start, 2019 frames
row 6713: window alarm end, 280 ms after the row was made
row 6797: alarm end, 0 ms after the row was made
row 6797: window alarm start, 90 ms after the row was made
row 6797: window alarm frames stored, 177 ms after the window alarm start, 2020 frames
row 6807: window alarm end, 180 ms after the row was made
sent 50001, echoed 50001, late ms median 0.000, p99 0.000, max 1.419
```

ボードの行は起動してから数えるので、6.2 の PC の行に一定の差を足したものになる。差は
最初の `window alarm start` の行から 201 を引けば分かる。上の例では 6704 − 201 = 6503 である。

| 6.2 の PC の行 | PC の行 + 差 | 上の例のボードの行 |
|---|---|---|
| `0x0CFF0180 start at row 201` | 6704 | `row 6704: window alarm start` |
| `0x0CFF0080 start at row 210` | 6713 | `row 6713: alarm start` |
| `0x0CFF0180 end at row 211` | 6714 | `row 6713: window alarm end`。窓の警報は行の警報が鳴っている行では鳴らないので、行の警報が始まる行で終わる |
| `0x0CFF0080 end at row 295` | 6798 | `row 6797: alarm end` |
| `0x0CFF0180 start at row 295` | 6798 | `row 6797: window alarm start` |
| `0x0CFF0180 end at row 305` | 6808 | `row 6807: window alarm end` |

ボードが行を作る時刻は送り始めと揃っていないので、1 行程度ずれることがある。
`frames stored` が警報が始まるたびに 1 つ出て、最後の行の `echoed` が `sent` と同じなら正しく動いている。
警報が鳴っている間はボードの緑の LED（LD2）が光る。光り方は [ボードの手順の 7.2.1.1](../guidelines/board_guide_ja.md#7211-led) にある。
ほかの行の読み方は [ボードの手順の 7.2.1](../guidelines/board_guide_ja.md#721-ボードにフレームを送る) にある。

ボードは警報が鳴るたびに、その前のフレームをバンク 2 に記録する。記録できるのは 8 回分で、
`both_alarms.parquet` を 1 回送ると 3 回分を使う。続けて送ると途中から記録されなくなるので、
2 回目からは送る前に `erase_bank_2` を実行して記録を消す。詳しくは [ボードの手順の 7.1.3](../guidelines/board_guide_ja.md#713-flash-のバンク-2-を消す) にある。

窓の警報だけが出るログを送るときは、`expected_window_alarm` と `send_window_alarm` を使う。

## 7. Flash の記録を見る

送り終えてから `read_bank_2_both_alarms` を実行する。バンク 2 を `bank2.bin` に読み出し、
送ったログと突き合わせる。読み方は [ボードの手順の 7.2.2](../guidelines/board_guide_ja.md#722-flash-の記録を見る) にある。
`send_window_alarm` を送ったあとは `read_bank_2_window_alarm` を使う。
