#!/usr/bin/env perl

# Copyright (c) 2020 Atsuo Yamada
#
# This software is provided 'as-is', without any express or implied
# warranty. In no event will the authors be held liable for any damages
# arising from the use of this software.
#
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
#
#    1. The origin of this software must not be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but is not required.
#
#    2. Altered source versions must be plainly marked as such, and must not be
#    misrepresented as being the original software.
#
#    3. This notice may not be removed or altered from any source
#    distribution.

# zlibライセンスです( https://ja.wikipedia.org/wiki/Zlib_License )



use strict;
use warnings;
use utf8;
use CGI;


# 内容を更新したら忘れずにバージョンを上げる事
my $version_rmch = "1.0.2";



# 設定項目
my $tmpdir = "/tmp";
my $is_verbose = 0;
my $default_pngquant_quality = 90;
my $size_limit = 512;





sub basename {
  my ($path) = @_;
  $path =~ s/^(.*[\/\\])//;
  return $path;
}

sub emit_content {
  print "Content-Type: $_[0]\n";
  print "Pragma: no-cache\n";
  print "\n";
  print $_[1];
}


sub emit_html {
  binmode(STDOUT, ":utf8");
  emit_content("text/html; charset=utf-8", $_[0]);
}


sub emit_text {
  binmode(STDOUT, ":utf8");
  emit_content("text/plain; charset=utf-8", $_[0]);
}

sub sh {
  my ($line) = @_;
  if ($is_verbose) {
    warn("sh: $line\n");
    $line = "$line 1>&2";
  }
  else {
    $line = "$line > /dev/null 2>&1";
  }
  return (system($line) == 0);
}



my $version_imagemagick = `convert -version 2>&1`;
my $has_imagemagick = !$?;
if ($has_imagemagick) {
  $version_imagemagick = (split(/\s/, $version_imagemagick))[2];
}
else {
  $version_imagemagick = "(not installed)";
}

my $version_pngquant = `pngquant --version 2>&1`;
my $has_pngquant = !$?;
if ($has_pngquant) {
  chomp($version_pngquant);
}
else {
  $version_pngquant = "(not installed)";
}



my $cginame = basename(__FILE__);

my $html = sub { local $/; my $t = <DATA>; return $t; }->();
$html =~ s/__FILE__/$cginame/g;
$html =~ s/__HAS_PNGQUANT__/$has_pngquant/g;
$html =~ s/__SIZE_LIMIT__/$size_limit/g;
$html =~ s/__VERSION_RMCH__/$version_rmch/g;
$html =~ s/__VERSION_IMAGEMAGICK__/$version_imagemagick/g;
$html =~ s/__VERSION_PNGQUANT__/$version_pngquant/g;






sub str2uint {
  my ($s) = @_;
  if (!$s) { return 0; }
  if ($s =~ /\D/) { return 0; }
  return 0+$s;
}

sub is_even {
  my ($v) = @_;
  return !($v % 2);
}

sub do_rmch {
  my ($path_prefix, $srcpath, $resultpath, $is_rightward, $resize_x, $resize_y, $quality) = @_;

  if ($resize_x && $size_limit < $resize_x) { $resize_x = $size_limit; }
  if ($resize_y && $size_limit < $resize_y) { $resize_y = $size_limit; }
  if ($resize_x && !$resize_y) {
    $resize_y = 100000;
  }
  if (!$resize_x && $resize_y) {
    $resize_x = 100000;
  }
  $quality = str2uint($quality);
  if (!$quality) {
    $quality = $default_pngquant_quality;
  }

  my $need_resize = $resize_x && $resize_y && 1;

  my $convert_args = "";
  if ($is_rightward) { $convert_args .= " -flop"; }
  # -resizeはぼやけてしまうので、同時に-unsharpするとよいらしい…
  # (ただ、誤った輪郭線が出る原因にもなり得るので難しいところ)
  if ($need_resize) {
    $convert_args .= " -unsharp 0 -resize ${resize_x}x${resize_y}";
  }

  my $tmp_left = $path_prefix . "tmp_rmch_left.png";
  my $tmp_left2 = $path_prefix . "tmp_rmch_left2.png";
  my $tmp_right = $path_prefix . "tmp_rmch_right.png";
  my $tmp_row_left = $path_prefix . "tmp_rmch_row_left.png";
  my $tmp_row_right = $path_prefix . "tmp_rmch_row_right.png";

  unlink $tmp_left;
  unlink $tmp_left2;
  unlink $tmp_right;
  unlink $tmp_row_left;
  unlink $tmp_row_right;

  my $is_failed = 0;

  sh("convert ${srcpath} ${convert_args} ${tmp_left}") or ($is_failed = 1);

  if ($need_resize && !$is_failed) {
    my $line = `identify $tmp_left`;
    # foo.png PNG 667x827 667x827+0+0 8-bit sRGB 10395B 0.000u 0:00.000
    if ($line =~ /PNG (\d+)x(\d+)/) {
      my $w = 0+$1;
      my $h = 0+$2;
      my $need_inc_w = is_even($resize_x) && !is_even($w);
      my $need_inc_h = is_even($resize_y) && !is_even($h);
      if ($need_inc_w) { $w++; }
      if ($need_inc_h) { $h++; }
      if ($need_inc_w || $need_inc_h) {
        sh("convert ${tmp_left} -background none -gravity southwest -extent ${w}x${h} ${tmp_left2}") or ($is_failed = 1);
        sh("cp ${tmp_left2} ${tmp_left}") or ($is_failed = 1);
      }
    }
    else {
      # identifyが失敗した等の理由でこっちに来る場合あり
      if ($is_verbose) {
        warn("failed identify: $line");
      }
      $is_failed = 1;
    }
  }

  $is_failed or sh("convert ${tmp_left} -flop ${tmp_right}") or ($is_failed = 1);
  $is_failed or sh("convert +append ${tmp_left} ${tmp_left} ${tmp_left} ${tmp_row_left}") or ($is_failed = 1);
  $is_failed or sh("convert +append ${tmp_right} ${tmp_right} ${tmp_right} ${tmp_row_right}") or ($is_failed = 1);

  # 上から down left right up の順
  $is_failed or sh("convert -append ${tmp_row_left} ${tmp_row_left} ${tmp_row_right} ${tmp_row_right} ${resultpath}") or ($is_failed = 1);

  if ($has_pngquant) {
    $is_failed or sh("pngquant --ext .png -f --speed 1 --quality ${quality} --strip 256 ${resultpath}");
  }

  unlink $tmp_left;
  unlink $tmp_left2;
  unlink $tmp_right;
  unlink $tmp_row_left;
  unlink $tmp_row_right;

  return !$is_failed;
}


sub emit_png {
  my ($path, $filename) = @_;

  $filename =~ s/[^-\w\.\!]/_/g;
  $filename = '$' . $filename;

  my $filesize = -s $path;

  open(IMG, $path);
  binmode(IMG);
  print "Content-Type: application/octet-stream\n";
  print "Content-Disposition: attachment; filename=\"$filename\"\n";
  print "Content-Length: $filesize\n";
  print "\n";
  print <IMG>;
  close IMG;
}


sub main {
  binmode(STDIN);
  binmode(STDOUT);
  binmode(STDERR);

  if (!$has_imagemagick) {
    return emit_text("サーバにimagemagickがインストールされていないので動きません");
  }

  my $q = CGI->new;
  $q->charset("utf-8");

  my $param = $q->{"param"};

  my $uploadfilepath = $param->{"file"}->[0];

  if (!$uploadfilepath) {
    emit_html($html);
    return;
  }

  my $uploadfilename = basename($uploadfilepath);

  my $uploadfileext = $uploadfilename;
  $uploadfileext =~ s/^(.*\.)//;

  if ($uploadfileext ne "png") {
    emit_text("pngファイル以外は処理できません($uploadfilepath,$uploadfilename,$uploadfileext)");
    return;
  }

  my $is_rightward = str2uint($param->{"is_rightward"}->[0]);
  my $resize_x = str2uint($param->{"resize_x"}->[0]);
  my $resize_y = str2uint($param->{"resize_y"}->[0]);
  my $quality = str2uint($param->{"quality"}->[0]);
  #emit_text("is_rightward=$is_rightward, resize_x=$resize_x, resize_y=$resize_y, quality=$quality"); return;

  my $path_prefix = $tmpdir . "/rmch_" . $$ . "_";
  my $srcpath = $path_prefix . "uploaded.png";
  my $resultpath = $path_prefix . "result.png";

  open(WF, '>'.$srcpath);
  binmode WF;
  while (read($uploadfilepath, my $buf, 256)) { print WF $buf; }
  close(WF);

  my $is_succeeded = do_rmch($path_prefix, $srcpath, $resultpath, $is_rightward, $resize_x, $resize_y, $quality);

  unlink $srcpath;

  if ($is_succeeded) {
    emit_png($resultpath, $uploadfilename);
  }
  else {
    emit_text("画像ファイルの処理に失敗しました");
  }

  unlink $resultpath;
}


main();
exit 0;

__DATA__
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8" />
<meta name="robots" content="noindex,nofollow,noarchive" />
<title>__FILE__</title>
<style type="text/css"><!--
.dropover {
  background-color: #ddf;
}
.rightward-selector {
  margin: 0.5em;
  font-size: 1.5em;
}
#submit-button {
  margin: 0.5em;
  padding: 0.5em;
  font-size: 2em;
}
#preview-canvas {
  background: repeat url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAARUlEQVRYhe3OsQ0AMAgDQaZlJ0+bbIALhNx84fLlK0lvWneP2/YFAACAOOD6wPUAAADIA64PXA8AAIA84PrA9QAAAIgDPiff9ohU584/AAAAAElFTkSuQmCC");
  border: solid 4px #000;
  margin: 0.5em;
  padding: 0;
}
--></style>
</head>
<body>
<form enctype="multipart/form-data" method="POST" action="__FILE__" id="form">
<h3>一枚絵の<code>hoge.png</code>からツクール形式の<code>img/characters/$hoge.png</code>を生成するやつ</h3>
<div>この辺にpngファイルを放り込む(ドラッグ＆ドロップ可能)</div>
<div><input id="upload-file" name="file" type="file" /></div>
<div><canvas id="preview-canvas" width="200" height="200"></canvas></div>
<div>横<input type="text" name="resize_x" value="" />px、縦<input type="text" name="resize_y" value="" />pxに収まるサイズにアスペクト比維持しつつ拡大縮小してから処理する<br />(片方だけ指定するのがおすすめ、偶数指定推奨、上限__SIZE_LIMIT__pxまで、両方無指定なら上限突破可能)</div>
<div class="rightward-selector">
<label><input type="radio" name="is_rightward" value="0" checked="checked" />元画像は左向き</label>
<span>　　</span>
<label><input type="radio" name="is_rightward" value="1" />元画像は右向き</label>
</div>
<div>(注意：サイズが大きいほど生成に時間かかります)</div>
<div><input id="submit-button" type="submit" value="生成する！" disabled="disabled" /></div>
<div class="status">
[rmch version: __VERSION_RMCH__]
[imagemagick version: __VERSION_IMAGEMAGICK__]
[pngquant version: __VERSION_PNGQUANT__]
</div>
</form>
<script>

function displayError (msg) {
  // TODO: エラーメッセージ表示の改善
  alert(msg);
}

var uploadFile = document.getElementById("upload-file");
var previewCanvas = document.getElementById("preview-canvas");

function setDisableSubmitButton (b) {
  document.getElementById("submit-button").disabled = !!b;
}

setDisableSubmitButton(true);

document.getElementById("form").addEventListener("submit", function (e) {
  document.getElementById("submit-button").blur();
});


function showDropping () {
  document.body.classList.add('dropover');
}
function hideDropping () {
  document.body.classList.remove('dropover');
}

document.body.addEventListener('dragover', function (e) {
  e.preventDefault();
  e.dataTransfer.dropEffect = 'copy';
  showDropping();
  return false;
});
document.body.addEventListener('dragleave', function (e) {
  e.preventDefault();
  hideDropping();
});

function loadFile (file) {
  function errorEnd (msg) {
    uploadFile.value = "";
    previewCanvas.getContext("2d").clearRect(0, 0, previewCanvas.width, previewCanvas.height);
    displayError(msg);
    setDisableSubmitButton(true);
    return;
  }
  if (!file.type.match(/image\/png/)) {
    return errorEnd("pngファイル以外は処理できません");
  }
  var image = new Image();
  var reader = new FileReader();

  function onLoaded (imageSrc) {
    var originalW = imageSrc.width;
    var originalH = imageSrc.height;
    var aspectRate = originalW / originalH;
    var defaultCssCanvasW = 200;
    var defaultCssCanvasH = 200;
    var cssCanvasW = Math.round(defaultCssCanvasW * aspectRate);
    var cssCanvasH = defaultCssCanvasH;
    previewCanvas.width = originalW;
    previewCanvas.height = originalH;
    previewCanvas.style.width = cssCanvasW + "px";
    previewCanvas.style.height = cssCanvasH + "px";
    var ctx = previewCanvas.getContext("2d");
    ctx.drawImage(imageSrc, 0, 0, originalW, originalH, 0, 0, originalW, originalH);
    setDisableSubmitButton(false);
  }

  reader.onload = function (e) {
    image.onload = function () { onLoaded(image); };
    image.src = e.target.result;
  };
  reader.onerror = function (e) {
    return errorEnd("ファイルの読み込みに失敗しました");
  };
  reader.readAsDataURL(file);
}

document.body.addEventListener('drop', function (e) {
  e.preventDefault();
  hideDropping();
  var files = e.dataTransfer.files;
  uploadFile.files = files;
  loadFile(files[0]);
  return false;
}, false);

uploadFile.addEventListener('change', function (e) {
  hideDropping();
  var files = uploadFile.files;
  if (files[0]) {
    loadFile(files[0])
  } else {
    setDisableSubmitButton(true);
  }
}, false);


</script>
<hr />
<p><b>注意：これは「画像をサーバに送信して処理する奴」です。サーバの負荷が結構すごいので、不特定多数の人にurlを知られないよう注意してください(悪意のある人はサーバを屈服させる事が可能です…)。</b></p>
<p>ソースコードを<a href="https://github.com/ayamada/rmch" target="_blank">github</a>にて公開しています。個人のサーバに設置して動かす事が可能です(要imagemagick)。</p>
<p>サーバにpngquantがインストールされている場合、これを使って減色しファイルサイズを軽量化します。</p>
<p>偶数指定で拡大縮小指定した場合に限り、拡大縮小後の縦サイズか横サイズが奇数になった場合は1ドット分の透明ラインを追加し、偶数になるよう補正します。</p>
</body>
</html>
