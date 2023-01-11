# cam_autofocus

## はじめに
Arducam B0181のピントがあった状態で画質を確認するようにします。

## requirement
- Jetson Nano
    - python 3.6 or above
    - libopencv-python
    - python3-numpy
    - v4l2loopback-dkms, v4l2loopback-utils

## V4L2 Loopbackのセットアップ
v4l2loopbackのインストールと設定が必要です。
次の手順を実行してください。

1. `sudo apt install v4l2loopback-dkms v4l2loopback-utils`
1. `echo v4l2loopback | sudo tee -a /etc/modules`
1. `echo "options v4l2loopback devices=12" |  sudo tee -a /etc/modprobe.d/v4l2loopback.conf`

## serviceのインストール
systemd ディレクトリの install_gst_start.sh を実行します。
gstreamerを起動するために Jetson Nanoを再起動するか、
`sudo systemctl start gst_start.service`
を実行します。

## 使用方法
check_cam.py を実行します。
`input camera serial number: `
と表示されたら、カメラのシリアル番号を入力し RETERN キーを押下してください。
ピントを合わせる動作をし、ピントがあったときの画像が Check ディレクトリに保存されます。

カメラのシリアル番号としては、カメラを認識できるIDとしての意味しかありません。
任意の番号を入力してください。
