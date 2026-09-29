# ボードで動かす手順

NUCLEO-H533RE の上で μT-Kernel 3.0 ([mtk3_bsp2](https://github.com/tron-forum/mtk3_bsp2))
を動かし、CAN バスから受けたフレームで異常を検知するまでの手順。

## 必要なもの

| もの | 型番 |
|---|---|
| マイコンボード | STMicroelectronics NUCLEO-H533RE |
| CAN トランシーバ | Microchip MCP2562FD-E/P (8 ピン DIP) |
| USB-CAN アダプタ | DSD TECH SH-C31A (candleLight ファームウェア) |
| 終端抵抗 | 120 Ω を 2 本 |
| USB ハブ | USB 2.0 のもの。Apple シリコンの Mac に直接挿すと ST のツールが ST-LINK との通信でタイムアウトする |

### ソフトウェア

ST のツールはすべて st.com から OS 用の公式インストーラをダウンロードして入れる。
ダウンロードには st.com へのログインが要る。Ubuntu の apt にはない。

| もの | 版 | macOS | Ubuntu |
|---|---|---|---|
| STM32CubeMX | 6.17.0 (STM32CubeMX2 ではない) | macOS 用のインストーラ | `stm32cubemx-lin-v6-17-0.zip` の `SetupSTM32CubeMX-6.17.0` を開く |
| STM32Cube FW_H5 | V1.6.0 | CubeMX の Help、Manage embedded software packages で入れる | macOS と同じ |
| STM32CubeIDE | 2.1.1 | `st-stm32cubeide_2.1.1_28236_20260312_0043_aarch64.dmg.zip` | `st-stm32cubeide_2.1.1_28236_20260312_0043_amd64.deb_bundle.sh.zip` の中身を `sudo sh` で実行する |
| STM32CubeProgrammer | 2.23.0。コマンドラインの `STM32_Programmer_CLI` を使う | macOS 用のインストーラ | `SetupSTM32CubeProgrammer_linux_64.zip` の `SetupSTM32CubeProgrammer-2.23.0.linux` を開く |
| ST-LINK のファームウェア | 新品のボードは最初に更新する | CubeProgrammer の ST-LINK の Firmware upgrade で行う | macOS と同じ |
| ST Edge AI Core | 4.0.1。モデルの実行ライブラリを 7.1 の手順で使う | macOS 用のインストーラで、STM32 MCU のコンポーネントを選ぶ | `stedgeai-lin.zip` の `stedgeai-linux-onlineinstaller` を開き、STM32 MCU のコンポーネントを選ぶ |
| Python | 3.9 | [モデルを作る手順](pipeline_guide_ja.md#python-を用意する) で用意する | macOS と同じ |
| libusb | | `brew install libusb` | 要らない |

### Ubuntu で入れるときに気をつけること

ST Edge AI Core のインストーラは、Ubuntu にない Qt の xcb のライブラリを使うので、先に入れる。

```sh
sudo apt install libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0
```

ST-LINK を root なしで使う udev ルールは CubeIDE のインストーラが入れる。入れた後に
ボードを挿し直し、sudo なしで SWD につながることを確かめる。`Board : NUCLEO-H533RE` が出ればよい。

```sh
~/STMicroelectronics/STM32Cube/STM32CubeProgrammer/bin/STM32_Programmer_CLI -c port=SWD
```

CubeMX は最初の起動で数分パッケージの一覧を取るので、その間に FW_H5 を入れようとすると `The update is already in use` と出る。待ってから開き直す。

## 1. CubeMX でプロジェクトを作る

できあがる設定は [board/cubemx/ai_can_detection.ioc](../board/cubemx/ai_can_detection.ioc)
にある。この `.ioc` を CubeMX で開けば以下の操作は済んだ状態になる。

### ボードを選ぶ

1. Access to Board Selector を開き、`NUCLEO-H533RE` を選んで Start Project を押す。
   TrustZone を使うか聞かれたら無効にする。

2. Project Manager タブで次のように設定する。

   | 項目 | 値 |
   |---|---|
   | Project Name | 任意。以下の例では `ai_can_detection` |
   | Project Location | このリポジトリの外の任意のディレクトリ。以下の例では `~/NUCLEO-H533RE` |
   | Toolchain/IDE | `STM32CubeIDE`。Generate Under Root にチェック |

### FDCAN1 のピン

Pinout & Configuration タブのピン配置図で、PB8 をクリックして `FDCAN1_RX` を、PB7
をクリックして `FDCAN1_TX` を選ぶ。

### FDCAN1 のパラメータ

Connectivity の FDCAN1 で Mode の Activated にチェックを入れ、Parameter Settings
を次のようにする。表にない項目は初期値のまま。

| 項目 | 値 |
|---|---|
| Frame Format | Classic mode |
| Mode | Normal mode |
| Auto Retransmission | Enable |
| Nominal Prescaler | 2 |
| Nominal Sync Jump Width | 8 |
| Nominal Time Seg1 | 55 |
| Nominal Time Seg2 | 8 |

FDCAN のクロック 32 MHz から、250 kbit/s でサンプルポイント 87.5% になる値である。

### 受信割り込み

System Core の NVIC で `FDCAN1 interrupt 0` の Enabled にチェックを入れ、Preemption
Priority を 1 にする。μT-Kernel の割り込み禁止がこの割り込みも止める優先度である。

### クロック

Clock Configuration タブで次のように設定する。SYSCLK と APB1 は初期値の 32 MHz
のまま。

| 項目 | 値 |
|---|---|
| PLL Source Mux | CSI (4 MHz) |
| PLL1 の N | 128 |
| PLL1 の Q | 16 |
| FDCAN Clock Mux | PLL1Q |

FDCAN のクロックを APB1 と同じ 32 MHz にする。APB1 より速いと受信したフレームを取りこぼす。

### コードを生成する

Generate Code を押す。出てくるポップアップでは BSP の項目をすべてチェックし、
次のポップアップは閉じる。

## 2. 配線

MCP2562FD の各ピンを次のようにつなぐ。CN7 と CN10 は NUCLEO-H533RE の ST morpho
コネクタで、ピン番号は UM3121 の Table 17 による。

| MCP2562FD のピン | つなぐ先 |
|---|---|
| 1 TXD | CN10 の 5 番、PB7 |
| 2 VSS | GND、CN7 の 20 番 |
| 3 VDD | CN7 の 18 番、5V |
| 4 RXD | CN10 の 36 番、PB8 |
| 5 VIO | CN7 の 16 番、3V3 |
| 6 CANL | USB-CAN アダプタの CANL |
| 7 CANH | USB-CAN アダプタの CANH |
| 8 STBY | GND |

VIO がロジックの電圧をボードの 3.3 V に合わせる。STBY を High にすると送信しなくなる。

バスの両端に 120 Ω を 1 本ずつ入れ、USB-CAN アダプタの GND もボードと同じ GND に
つなぐ。

## 3. USB-CAN アダプタ

### macOS

macOS にはこのアダプタのドライバがないので、リポジトリの送信スクリプトは
`requirements.txt` で入る `pyusb` と `gs_usb` で USB から直接動かす。`pyusb` が使う
libusb を入れておく。

```sh
brew install libusb
```

送信スクリプトは、python-can を通さず `gs_usb` で 250 kbit/s のビットタイミングを直接設定する。

### Ubuntu

`can-utils` を入れ、アダプタを `can0` として 250 kbit/s で立ち上げる。最後の
コマンドはバスに流れるフレームを表示する。

```sh
sudo ip link set can0 type can bitrate 250000 sample-point 0.875
sudo ip link set can0 up
candump -t d -e can0
```

サンプルポイント 0.875 はボードの FDCAN1 の設定に合わせている。

リポジトリの送信スクリプトは、立ち上げた `can0` から送る。

## 4. mtk3_bsp2 とアプリケーションをプロジェクトに入れる

CubeMX が生成したプロジェクトに `board.prepare` で mtk3_bsp2 とアプリケーションを
加える。最後の引数は `board/application/` の下のフォルダ名で、ビルドするアプリ
ケーションを選ぶ。パッチを当てた mtk3_bsp2 `1ab52cc` を取得し、`main.c` に
カーネルの起動を入れ、アプリケーションと `board/lib/` をプロジェクトにリンクする。

```sh
cd ~/ai_can_detection
python3 -m board.prepare ~/NUCLEO-H533RE/ai_can_detection alive
```

CubeIDE でプロジェクトを開いている間は実行しない。CubeIDE が開いている間にプロ
ジェクトのファイルを書き換える。別のアプリケーションに替えるときは、CubeIDE で
プロジェクトを閉じてから実行し直す。CubeMX でコードを生成し直したときも実行し直す。

`board.prepare` はパッチを `git am` で当てるので、git に名前とメールアドレスが要る。
設定していないと `Committer identity unknown` で止まる。

```sh
git config --global user.name "名前"
git config --global user.email "メールアドレス"
```

`board/patches` のパッチが変わったときや、上のように途中で止まったときは、
プロジェクトの mtk3_bsp2 に古いパッチが当たったままか、パッチが当たっていない。
`board.prepare` は `mtk3_bsp2 lacks <パッチ名>` で止まる。mtk3_bsp2 を `1ab52cc` に
戻してパッチを当て直し、`board.prepare` を実行し直す。

```sh
git -C ~/NUCLEO-H533RE/ai_can_detection/mtk3_bsp2 reset --hard 1ab52cc
git -C ~/NUCLEO-H533RE/ai_can_detection/mtk3_bsp2 am --keep-cr board/patches/*.patch
```

## 5. ビルドと書き込み

書き込みはコマンドラインか CubeIDE のどちらかで行う。

### コマンドラインで行う

CubeIDE と `STM32_Programmer_CLI` の場所を、`board/flash.json` に書いておく。

```json
{
  "cubeide": "/Applications/STM32CubeIDE.app/Contents/MacOS/STM32CubeIDE",
  "programmer": "/path/to/STM32_Programmer_CLI"
}
```

Ubuntu で既定の場所に入れたときは次のようになる。

```json
{
  "cubeide": "/opt/st/stm32cubeide_2.1.1/stm32cubeide",
  "programmer": "~/STMicroelectronics/STM32Cube/STM32CubeProgrammer/bin/STM32_Programmer_CLI"
}
```

CubeIDE を閉じてから、リポジトリのトップで実行する。

```sh
python3 board/flash.py ~/NUCLEO-H533RE/ai_can_detection
```

ビルドし、SWD で書き込んで照合し、マイコンをリセットする。

### CubeIDE で行う

1. File、Import、General、Existing Projects into Workspace を選び、プロジェクトの
   ディレクトリをルートにする。Copy projects into workspace にはチェックを入れない。
2. プロジェクトを選び、Project、Build Project を選ぶ。コンソールの最後に
   `Build Finished` とエラー 0 が出る。
3. Run、Run As、STM32 C/C++ Application を選ぶ。初回は起動設定のダイアログが開く。
   Debug probe は `ST-LINK (ST-LINK GDB server)` のまま OK を押す。コンソールの最後に
   `Download verified successfully` が出る。

### UART を見る

ST-LINK の仮想 COM ポートを、別のターミナルで `screen` で開く。macOS では
`/dev/cu.usbmodem` の後ろに番号が付き、挿し直すと変わることがある。

```sh
ls /dev/cu.usbmodem*
screen /dev/cu.usbmodem11202 115200   # macOS。ls で出た名前にする
screen /dev/ttyACM0 115200            # Ubuntu
```

`screen` を抜けるときは `Ctrl-A` を押してから `\`。

Ubuntu では、CubeIDE が入れた ST-LINK の udev ルールにより、読み書きできるのは
`plugdev` グループのユーザと、デスクトップにログインしているユーザになる。SSH で
つないだときも読めるように、`groups` で `plugdev` に入っていることを確かめる。
Ubuntu のインストール時に作ったユーザは最初から入っている。入っていなければ
`sudo usermod -aG plugdev $USER` で入れてログインし直す。

## 6. CAN バスを確かめる

`can_bus_debug` は FDCAN1 が受けたフレームをすべて UART に出し、ID `0x18FEF100`
のフレームを 1 秒ごとに送る。2 と 3 の手順でバスをつないでおき、4 と 5 の手順で
`can_bus_debug` を書き込む。

USB-CAN アダプタを Ubuntu で `can0` として立ち上げ、`candump` でバスを表示する。
ボードが送る `18FEF100` が 1 秒ごとに出る。

`cansend` でフレームを 1 つ送る。

```sh
cansend can0 18FEF200#1111111111111111
```

UART には、送ったフレームの ID とデータを持つ `CAN RX:` の行が出る。さらに 1 秒
ごとに次の行が出る。

```
CAN RX status: taken 1, printed 1, fifo 0, fifo lost 0, ram failed 0, rec 0, tec 0
```

`taken` は受信したフレームの数、`printed` は UART に出した数、`fifo lost` と
`ram failed` はフレームを捨てたとき 1、`rec` と `tec` は FDCAN1 のエラーカウンタ。

`taken` と `printed` が送ったフレームの数と同じになり、残りが 0 のままなら
バスは動いている。`FDCAN start error` が出たときは FDCAN1 が起動していない。
`send failed` が出たときは、ボードが送信するフレームを送信キューに入れられなかった。

## 7. 異常検知を動かす

2 と 3 の手順でバスと USB-CAN アダプタをつないでおく。

タスクの構成は [スライドの 9 枚目](https://docs.google.com/presentation/d/1hwYTSuzBjXj9xMCqELzK-VM9VE5GtPjH6FCRop7E4cI/edit#slide=id.p7) にある。

### 7.1 準備

1. Flash のバンク 2 を消す。最初に一度だけでよい。ボードはバンク 2 に残っているものを
   記録として読むので、消さずに動かすと前のデータを記録と取り違える。

   ```sh
   STM32_Programmer_CLI -c port=SWD -ob displ
   ```

   出てくるオプションバイトの `SWAP_BANK` が 0 であることを確かめる。1 のときは
   バンクが入れ替わっていて、次の消去がプログラムを消してしまうので、ここで止める。
   0 なら消す。セクタ番号は両方のバンクを通して数えるので、バンク 2 は 32 から 63 である。

   ```sh
   STM32_Programmer_CLI -c port=SWD -e '[32' '63]'
   ```

2. `ai_can_anomaly_detection` をプロジェクトに入れて書き込む。モデルの実行ライブラリを
   ST Edge AI Core から取るので、`/Applications/ST/STEdgeAI/4.0` 以外に入れたときは
   場所を渡す。環境変数 `STEDGEAI_ROOT` を実行するシェルで export しておくか、
   `board.prepare` に `--stedgeai-root` で渡す。両方あるときは `--stedgeai-root` が
   優先される。Ubuntu では `/opt/ST/STEdgeAI/4.0` に入る。

   ```sh
   export STEDGEAI_ROOT=/opt/ST/STEdgeAI/4.0   # Ubuntu
   ```

   ```sh
   python3 -m board.prepare ~/NUCLEO-H533RE/ai_can_detection ai_can_anomaly_detection
   python3 board/flash.py ~/NUCLEO-H533RE/ai_can_detection
   ```

   6 の手順と同じく UART を開く。`reading FDCAN1` が出れば受信を始めている。警報は
   UART ではなく CAN に出る。

   | UART に出たもの | 意味 |
   |---|---|
   | `FDCAN start error` | FDCAN1 が起動していない |
   | `flash store init error` | バンク 2 を読めず、そこで止まった |

3. 送るフレームを Hugging Face のデータ用リポジトリから取ってくる。約 2 GB あり、
   ログインは要らない。

   ```sh
   python3 -m board.application.ai_can_anomaly_detection.fetch
   ```

   `board/application/ai_can_anomaly_detection/fetched/frames/` に次の 2 つが入る。

   | ファイル | 中身 |
   |---|---|
   | `frames.parquet` | 攻撃を入れたログのフレーム。ログ 1 つは約 1 分 |
   | `attacked.json` | 各ログに入れた攻撃。`log` がログの名前、`pgn` が攻撃した PGN |

### 7.2 実行

ここでは `part_3/20210204093802472877.csv` を使う。行の警報も窓の警報も出るログである。
ほかのログは `attacked.json` の `log` から選ぶ。

1. PC で同じモデルを動かし、警報が始まる行と終わる行を出す。行は送り始めから 0.1 秒
   ごとに数える。

   ```sh
   python3 -m board.application.ai_can_anomaly_detection.expected part_3/20210204093802472877.csv
   ```

   ```
   alarm 0x0CFF0080 start at row 503
   alarm 0x0CFF0080 end at row 539
   alarm 0x0CFF0180 start at row 494
   alarm 0x0CFF0180 end at row 504
   alarm 0x0CFF0180 start at row 539
   alarm 0x0CFF0180 end at row 549
   ```

2. 3 の手順の USB-CAN アダプタから、同じログのフレームを記録された時刻の間隔で送る。約 1 分
   かかる。ボードが CAN に送ったフレームは `received at` の行に受け取った時刻とともに
   出る。7.3 で読むので `received_frames.txt` にも残す。

   ```sh
   python3 -m board.application.ai_can_anomaly_detection.send_test_frames part_3/20210204093802472877.csv | tee received_frames.txt
   ```

   ```
   sending 50001 frames from 1790683524.751
   received at 1790683574.256  CFF0180   [8]  01 7C 02 00 00 5A 00 FF
   received at 1790683574.434  CFF0480   [8]  7C 02 00 00 E2 07 FF FF
   ...
   sent 50001, echoed 50001, late ms median 0.000, p99 0.000, max 4.565
   ```

   最後の行の `echoed` が `sent` と同じなら、アダプタはすべてのフレームを送っている。
   `echoed` が 0 のときはアダプタが何も読めていないので、USB から抜き差しして送り直す。

### 7.3 結果

1. `board_frames` で `received_frames.txt` の `received at` の行を読み、ボードが送った
   フレームを 1 つずつ中身に直して出す。ほかの行は読み飛ばす。

   ```sh
   python3 -m board.application.ai_can_anomaly_detection.board_frames received_frames.txt
   ```

   ファイルの代わりに `-` を渡すと標準入力から読む。

   2026-09-29 に Release ビルド、32 MHz で動かしたときは次のように出た。

   ```
   row 636: window alarm start, 90 ms after the row was made
   row 636: window alarm frames stored, 178 ms after the window alarm start, 2018 frames
   row 637: window model late, finished 260 ms after the row was made, 0 rows lost before it
   ...
   row 646: alarm start, 0 ms after the row was made
   row 646: alarm frames stored, 175 ms after the alarm start, 2020 frames
   ...
   row 646: window alarm end, 360 ms after the row was made
   ...
   rows 647 to 679: window model late on 33 rows, 0 rows lost
   row 681: alarm end, 0 ms after the row was made
   row 681: window alarm start, 90 ms after the row was made
   row 681: window alarm frames stored, 179 ms after the window alarm start, 2019 frames
   ...
   row 691: window alarm end, 190 ms after the row was made
   ...
   ```

   | 見るところ | 正しいとき |
   |---|---|
   | `alarm` と `window alarm` の `start` と `end` の行 | ボードの行はボードが起動してから数えるので、PC の行に一定の差を足したものになる。上の例では差が 142 で、行の警報の始まりだけ 143。ボードが行を作る時刻は送り始めと揃っていないので、1 行ずれることはある |
   | `alarm start` の ms | 0。警報は窓モデルと保存に待たされていない |
   | `alarm frames stored` と `window alarm frames stored` | その警報の前のフレームを Flash に書き終えた。警報が始まるたびに 1 つ出る |
   | `window model late` | 窓モデルが次の行が来るまでに採点を終えられなかった行。遅れていない行は出ない |
   | `window model late on ... rows` | 窓モデルは遅れた後に追いついた。`0 rows lost` なら行を 1 つも失っていない |

   窓モデルが遅れる理由は [スライドの 11 枚目](https://docs.google.com/presentation/d/1hwYTSuzBjXj9xMCqELzK-VM9VE5GtPjH6FCRop7E4cI/edit?slide=id.p_realtime_conv#slide=id.p_realtime_conv) の優先度にある。

2. ボードを動かしたまま Flash のバンク 2 をファイルに読み出し、送ったログと突き合わせる。

   ```sh
   STM32_Programmer_CLI -c port=SWD mode=HOTPLUG -u 0x08040000 0x40000 bank2.bin
   python3 -m board.application.ai_can_anomaly_detection.read_alarm_frames bank2.bin --log part_3/20210204093802472877.csv
   ```

   ```
   area 0 sequence 0 window alarm row 636 frames 2018
     the MAC matches the one computed with the key
     matches log frames 39551 to 41568
   area 1 sequence 1 alarm row 646 frames 2020
     the MAC matches the one computed with the key
     matches log frames 40390 to 42409
   area 2 sequence 2 window alarm row 681 frames 2019
     the MAC matches the one computed with the key
     matches log frames 43333 to 45351
   ```

   記録ごとに、どちらの警報の記録か、MAC が鍵と合うか、送ったログのどのフレームと
   一致したかが出る。MAC が
   合い、ログのフレームと一致すれば正しく書けている。鍵は
   `board/lib/alarm_frames_mac/alarm_frames_mac_demo_key.h` にある。`--log` を付けなければ
   記録のフレームが出る。

   何を記録するかは [スライドの 8 枚目](https://docs.google.com/presentation/d/1hwYTSuzBjXj9xMCqELzK-VM9VE5GtPjH6FCRop7E4cI/edit#slide=id.p6) にある。

フレームと記録の形は
[ai_can_anomaly_detection の README](../board/application/ai_can_anomaly_detection/README.md)
にある。

Note: `ai_can_anomaly_detection` は、1 日 8 時間の使用で Flash のバンク 2 が 5 年もつ
ように、消去の間隔を自分で空けて書き込む。
