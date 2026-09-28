# ボードで動かす手順

NUCLEO-H533RE の上で μT-Kernel 3.0 ([mtk3_bsp2](https://github.com/tron-forum/mtk3_bsp2))
を動かし、CAN バスから受けたフレームで異常を検知するまでの手順。

## 必要なもの

| もの | 型番、版 |
|---|---|
| マイコンボード | STMicroelectronics NUCLEO-H533RE |
| CAN トランシーバ | Microchip MCP2562FD-E/P (8 ピン DIP) |
| USB-CAN アダプタ | DSD TECH SH-C31A (candleLight ファームウェア) |
| 終端抵抗 | 120 Ω を 2 本 |
| USB ハブ | USB 2.0 のもの。Apple シリコンの Mac に直接挿すと ST のツールが ST-LINK との通信でタイムアウトする |
| STM32CubeMX | 6.17.0 (STM32CubeMX2 ではない) |
| STM32Cube FW_H5 | V1.6.0 |
| STM32CubeIDE | 2.1.1 |
| STM32CubeProgrammer | コマンドラインの `STM32_Programmer_CLI` を使う |
| ST Edge AI Core | 4.0.1。モデルの実行ライブラリを 8 の手順で使う |
| Python | 3.9 |
| libusb | `brew install libusb` |

新品のボードは最初に ST-LINK のファームウェアを更新する。

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

macOS にはこのアダプタのドライバがないので、`pyusb` と `gs_usb` を入れる。

```sh
brew install libusb
python3 -m pip install --user pyusb gs_usb
```

リポジトリの送信スクリプトは、python-can を通さず `gs_usb` で 250 kbit/s のビットタイミングを直接設定する。

### Ubuntu

`can-utils` を入れ、アダプタを `can0` として 250 kbit/s で立ち上げる。最後の
コマンドはバスに流れるフレームを表示する。

```sh
sudo ip link set can0 type can bitrate 250000 sample-point 0.875
sudo ip link set can0 up
candump -t d -e can0
```

サンプルポイント 0.875 はボードの FDCAN1 の設定に合わせている。

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

## 5. ビルドと書き込み

書き込みはコマンドラインか CubeIDE のどちらかで行う。

### コマンドラインで行う (macOS)

CubeIDE と `STM32_Programmer_CLI` の場所を、`board/flash.json` に書いておく。

```json
{
  "cubeide": "/Applications/STM32CubeIDE.app/Contents/MacOS/STM32CubeIDE",
  "programmer": "/path/to/STM32_Programmer_CLI"
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

## 6. ボードが動くことを確かめる

`alive` は緑の LED を点滅させ、500 ms ごとに数を UART に出す。4 と 5 の手順で
`alive` を書き込み、ST-LINK の仮想 COM ポートを 115200 bps で開く。

```sh
ls /dev/cu.usbmodem*
screen /dev/cu.usbmodem11202 115200
```

`cu.usbmodem` の後ろの番号はボードをつなぎ直すと変わるので、`ls` が出したものを使う。

緑の LED が点滅し、次のように 1 行ずつ出れば動いている。

```
usermain 1
usermain 2
```

LED が消えたままで何も出ないときは、アプリケーションではなく mtk3_bsp2 の空の
`usermain` がビルドされている。

## 7. CAN バスを確かめる

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

## 8. 異常検知を動かす

`ai_can_anomaly_detection` は受信したフレームから 0.1 秒ごとに行を作り、ルールと
オートエンコーダで判定し、警報の始まりと終わりを FDCAN1 に送る。警報が始まるたびに、
その前のフレームを Flash のバンク 2 に書く。

### Flash のバンク 2 を消す

最初に一度だけ、SWD でバンク 2 を消す。書き込みの処理はバンク 2 に残っているものを
記録として読む。

```sh
STM32_Programmer_CLI -c port=SWD -ob displ
STM32_Programmer_CLI -c port=SWD -e '[32' '63]'
```

1 つ目のコマンドで出るオプションバイトの SWAP_BANK が 0 であることを確かめてから
消す。1 だと消去がプログラムに当たる。セクタ番号は両方のバンクを通して数える
ので、バンク 2 は 32 から 63 になる。

### 書き込む

4 と 5 の手順で `ai_can_anomaly_detection` を書き込む。モデルの実行ライブラリを
ST Edge AI Core から取るので、`/Applications/ST/STEdgeAI/4.0` 以外に入れたときは
`--stedgeai-root` で場所を渡す。

```sh
python3 -m board.prepare ~/NUCLEO-H533RE/ai_can_detection ai_can_anomaly_detection
python3 board/flash.py ~/NUCLEO-H533RE/ai_can_detection
```

UART に `reading FDCAN1` が出れば受信を始めている。`FDCAN start error` は FDCAN1
が起動していない。`flash store init error` はバンク 2 の記録を読めず、そこで止まって
いる。警報は UART ではなく CAN に出る。

### 送るフレームを取ってくる

攻撃を入れたテスト用のフレームを Hugging Face のデータ用リポジトリから取ってくる。
約 2 GB ある。ログインは要らない。

```sh
python3 -m board.application.ai_can_anomaly_detection.fetch
```

`board/application/ai_can_anomaly_detection/fetched/frames/` に `frames.parquet`
と `attacked.json` が入る。`attacked.json` は各ログに入れた攻撃で、`log` が
ログの名前、`pgn` が攻撃した PGN である。ログ 1 つは約 1 分のフレームである。

### PC での答えを出す

ログを 1 つ選び、PC で同じモデルを動かしたときに警報が始まる行と終わる行を出す。

```sh
python3 -m board.application.ai_can_anomaly_detection.expected part_3/20210204094457960567.csv
```

`alarm start at row` と `alarm end at row` の後に行番号が出る。行は送り始めから
0.1 秒ごとに数える。

### フレームを送って警報を受ける

3 の手順の macOS で、同じログのフレームを記録された時刻の間隔で送る。

```sh
python3 -m board.application.ai_can_anomaly_detection.send_test_frames part_3/20210204094457960567.csv
```

ボードが送った警報のフレームは、受け取った時刻とともに次のように出る。

```
received at 1790602535.128  CFF0080   [8]  01 82 02 00 00 FF FF FF
```

| バイト | 中身 |
|---|---|
| ID | 0x0CFF0080、拡張 ID。優先度 3、PGN 0xFF00、送信元アドレス 0x80 |
| 0 | 1 なら始まり、0 なら終わり |
| 1 から 4 | 行番号、リトルエンディアン |
| 5 から 7 | 0xFF |

ボードの行番号はボードが起動してから数えるので、PC の行番号に一定の差を足したもの
になる。最初の警報で差を求め、残りの警報をその差で PC の答えと比べる。ボードの tick
は送り始めと揃っていないので、1 行ずれることがある。

### Flash に書いた記録を読む

ボードを動かしたまま、バンク 2 をファイルに読み出す。

```sh
STM32_Programmer_CLI -c port=SWD mode=HOTPLUG -u 0x08040000 0x40000 bank2.bin
```

バンク 2 は 8 KB のセクタ 32 個で、1 セクタに記録が 1 つ入る。各セクタの先頭 16
バイトは書き込み順の番号と大きさのヘッダで、その後に記録が続く。値はすべて
リトルエンディアンである。

| バイト | 中身 |
|---|---|
| 0 から 3 | 警報が始まった行番号。警報のフレームと同じもの |
| 4 から 7 | フレームの数 |
| 8 から 15 | 0 |
| 16 から 47 | MAC。0 から 15 と、その後のフレームの HMAC-SHA256。鍵は `board/lib/alarm_frames_mac/alarm_frames_mac_demo_key.h` |
| その後 16 バイトずつ、古い順 | 前のフレームからのマイクロ秒 3 バイト、データの長さ 1 バイト、ID 4 バイト、データ 8 バイト。長さより後は 0 |

記録のフレームが、送ったフレームの一続きの部分と ID、長さ、データで一致すれば、
正しく書けている。送ったログと突き合わせるには次を動かす。

```sh
python3 -m board.application.ai_can_anomaly_detection.read_alarm_frames bank2.bin --log part_3/20210204094457960567.csv
```

記録ごとに、MAC が鍵と合うかと、一致した送ったフレームの番号が出る。`--log` を付けなければ記録のフレームが出る。
