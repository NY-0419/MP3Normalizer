# 音声一括ノーマライザー

MP3、M4A、WAV、FLACの音声を一括処理するWindows向け音声ノーマライザーです。
FFmpegの`loudnorm`フィルターを使用して、指定したラウドネスへ音量を調整します。

## 主な機能

- MP3 / M4A / WAV / FLACの入力
- MP3 / M4A (AAC / ALAC) / WAV / FLACの出力
- 入力形式に合わせた出力
- ラウドネス、トゥルーピークの指定
- MP3 / M4A (AAC)共通のビットレート設定
- M4A (ALAC)の可逆圧縮出力
- FLACの圧縮レベル設定
- アートワークの引き継ぎ
- プレビュー再生
- 選択曲のラウドネス・トゥルーピーク測定
- 処理途中のキャンセル
- 設定とログのAppData保存

## 起動方法

配布版はフォルダ構成を維持したまま、以下を実行してください。

```text
dist\MP3Normalizer\MP3Normalizer.exe
```

`MP3Normalizer.exe` だけを単独でコピーせず、`_internal`フォルダを含む`MP3Normalizer`フォルダ全体を配布してください。

## 使い方

1. 「ファイル追加」から音声ファイルを選択します。
2. 必要に応じて目標ラウドネスとトゥルーピークを設定します。
3. 「詳細設定」で保存方法と出力形式を選択します。
4. 出力先フォルダを指定します。
5. 「一括処理開始」を押します。

出力形式で「入力形式に合わせる」を選ぶと、入力ファイルと同じ形式で出力します。

## 設定とログ

設定とログは以下に保存されます。

```text
%APPDATA%\MP3Normalizer\settings.json
%APPDATA%\MP3Normalizer\app.log
```

## 対応形式と注意点

- WAVはコンテナ仕様上、アートワークを保持できません。
- 極端に短い音源や無音に近い音源は、ラウドネス測定の精度が限定されます。
- 出力形式を変更した場合、ラウドネス調整のため音声は再エンコードされます。
- 「ファイル名を変更しない」を選ぶと、出力先に元のファイル名（拡張子は出力形式に合わせる）で保存します。
- 入力元と出力先が同じフォルダの場合は、元ファイルが上書きされる可能性があるため確認が表示されます。
- 入力形式と出力形式が異なる場合は、元ファイルを残して`_norm`付きのファイルを作成します。

## 開発環境

必要なPythonパッケージをインストールします。

```powershell
python -m pip install -r requirements.txt
```

アプリを起動します。

```powershell
python main.py
```

テストを実行します。

```powershell
python -m unittest discover -s tests -v
```

## 配布版のビルド

PyInstallerをインストールして、ビルドスクリプトを実行します。

```powershell
python -m pip install -r requirements.txt
.\build.ps1
```

生成先:

```text
dist\MP3Normalizer\
```

ビルドには`ffmpeg\bin\ffmpeg.exe`と`image.ico`が必要です。

## FFmpegのライセンス

このアプリには、GPL v3で配布されるFFmpegビルドを同梱しています。
同梱FFmpegのライセンスとビルド情報は以下にあります。

```text
ffmpeg\LICENSE
ffmpeg\README.txt
```

FFmpegのソースコード情報は、同梱READMEに記載されています。再配布時はFFmpegおよび関連ライブラリのライセンス条件を確認してください。

## コード署名

現在の配布版はコード署名されていません。Windows SmartScreenの警告が表示される場合があります。
公開配布時は、配布元を確認したうえで実行してください。

配布ファイルの改ざん確認にはSHA-256ハッシュを使用できます。

```powershell
Get-FileHash .\dist\MP3Normalizer\MP3Normalizer.exe -Algorithm SHA256
```

## 無保証

このアプリは現状有姿（AS IS）で提供され、明示または黙示を問わず、特定目的への適合性、正確性、完全性、動作の継続性を含むいかなる保証も行いません。
本アプリの使用または使用不能によって生じたデータの損失、ファイルの破損、その他の損害について、開発者は責任を負いません。
重要な音声ファイルは、処理前に必ずバックアップを作成してください。

## ライセンス

このアプリ本体のライセンスは、配布形態に合わせて別途明記してください。
同梱FFmpegについては、`ffmpeg\LICENSE`および`ffmpeg\README.txt`を参照してください。

LGPL条件で配布するためのFFmpeg再ビルド要件は[FFMPEG-LGPL-BUILD.md](FFMPEG-LGPL-BUILD.md)に記載しています。現在同梱しているFFmpegはGPL v3版のため、LGPL版へ置き換えるまでLGPL版として配布しないでください。
