# LGPL版FFmpegの作成要件

現在の `ffmpeg/bin/ffmpeg.exe` はGPL v3のstatic buildです。LGPL条件で配布する前に、必ずLGPL互換構成でFFmpegを再ビルドし、`ffmpeg/bin` の実行ファイルとDLLを置き換えてください。

## 必須条件

- FFmpeg公式ソースの対応するリリースまたはコミットを取得する
- `--disable-gpl`
- `--disable-nonfree`
- `--enable-shared`
- `--disable-static`
- `libx264`、`libx265`、`libxvid`、`libfdk_aac`などGPL/nonfreeの外部ライブラリを有効化しない
- 使用する外部ライブラリのライセンスを個別に確認する
- 配布バイナリと完全に一致するソース、ビルド設定、変更差分を保存する

Windows向けの正確なconfigureコマンドは、使用するFFmpegのソース版、MSYS2/MinGW環境、外部ライブラリ構成が確定してから記録してください。存在しない構成をこの文書へ記載してはいけません。

## 配布前チェック

```powershell
ffmpeg\bin\ffmpeg.exe -buildconf
```

出力に次の項目がないことを確認します。

```text
--enable-gpl
--enable-nonfree
--enable-static
--enable-libx264
--enable-libx265
--enable-libxvid
--enable-libfdk_aac
```

`build.ps1`にも同じ検査があり、条件を満たさないFFmpegでは配布ビルドを停止します。

## ソース配布

対応するFFmpegソースをzipまたはtarballで配布し、バイナリと同じ公開場所からダウンロードできるようにします。ソースのコミットID、configure設定、変更差分、使用した外部ライブラリのライセンスを記録してください。

LGPLの最終的な適用判断は、実際のFFmpegビルド構成と販売形態を確認したうえで、専門家へ確認してください。