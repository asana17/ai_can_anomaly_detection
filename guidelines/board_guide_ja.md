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
