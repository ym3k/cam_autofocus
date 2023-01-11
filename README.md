# cam_autofocus

## はじめに
Arducam B0181のピントがあった状態で画質を確認するようにします。

## requirement
- Jetson Nano
    - python 3.6 or above
    - libopencv-python
    - python3-numpy

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
