# rmch.cgi

## これ何？

「一枚絵の `hoge.png` からツクール形式の `img/characters/$hoge.png` を生成するやつ」です。ツクールさわらない人には意味がありません。


## どう使うの？

サーバに設置してアクセスしてください(要imagemagick)。


## 利用手順

1. がんばって「cgiの動くhttpdと、imagemagickがインストールされた個人サーバ」を用意してください(共有サーバは避けてください)。pngquantもインストールされていればより良いですが必須ではありません。
2. ここに置いてある[rmch.cgi](https://raw.githubusercontent.com/ayamada/rmch/master/rmch.cgi)ファイルをダウンロードし、cgiの動作する場所に置いてください。そして実行権限をつけてください(具体的には `chmod a+x rmch.cgi` とか `chmod 755 rmch.cgi` とかみたいな奴です)。
3. ブラウザからアクセスしてください。
4. ファイルを投入し、必要ならパラメータをいじり、生成ボタンを押してください。


## 質問とかある

githubページの上の方にある「Issues」のところの中にある「New issue」ボタンからお願いします。日本語でokです。


## 更新履歴

- version 1.0.1 (2020/08/29)
    - ちょっとした文言の改善

- version 1.0.0 (2020/08/29)
    - 公開
