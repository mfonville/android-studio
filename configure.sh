#!/bin/bash
TOP="$(realpath .)"
export DEBFULLNAME="Maarten Fonville"
export DEBEMAIL="maarten.fonville@gmail.com"

for t in "wget" "sha256sum" "awk" "grep" "sed"; do
  if ! command -v $t >/dev/null 2>&1; then
    echo "$t is required but is not installed."; exit 1
  fi
done

d="$1"
case "$d" in
  trusty) trustydep=", lib32bz2-1.0 [amd64]";;
  xenial|artful|bionic);;
  clean) rm -f "$TOP/android-studio/debian/control" "$TOP/android-studio/debian/changelog" "$TOP/android-studio/debian/changelog.dch" "$TOP/android-studio/debian/preinst"; echo "Android Studio sources cleaned!"; exit 0;;
  *) echo "Unrecognized Ubuntu version, use a valid distribution as 1st argument"; exit 1;;
esac

c="$2"
case "$c" in
  stable)  suf="";;
  preview) suf="-$c";;
  *) echo "Unrecognized release channel, use a valid Android Studio release channel as 2nd argument"; exit 1;;
esac

# keep the conflict definitions with the beta, dev and canary for during the migration period
con="$(echo "android-studio, android-studio-beta, android-studio-dev, android-studio-canary, android-studio-preview, " | sed -e "s/android-studio$suf, //")"
con=${con::-2}

page="$(wget -O - -q "https://developer.android.com/studio/archive.html")"
frame="$(wget -O - -q "$(echo "$page" | awk 'BEGIN { RS = "<iframe data-src=\"" ; FS = "\" class" }  {print $1}' | tail -n 1)")"


case "$c" in
  stable) details="$(echo "$frame" | awk 'BEGIN { RS = "<section class=\"expandable" ; FS = "</section>" } /stable">.*<div class="downloads".*/  {print $1;exit;}')";;
  preview)details="$(echo "$frame" | awk 'BEGIN { RS = "<section class=\"expandable" ; FS = "</section>" } /<div class="downloads".*/  {print $1;exit;}')";;
esac

vername="$(echo "$details" | grep -oE '<p class="expand-control">.*' | cut -c 27-)"
dl="$(echo "$details" | grep -oE 'href="https://dl.google.com/dl/android/studio/ide-zips/[^"]+-linux.zip"')"
dl=${dl:6:-1}
ver="$(echo "$dl" | sed -n 's/.*android-studio-ide-\([0-9\.]*\)-linux\.zip/\1/p')"
sha="$(echo "$details" | sed -n "s/\([0-9a-f]*\) android-studio-ide-$ver-linux.zip/\1/p")"

if [ -z "$ver" ]; then
  echo "Could not parse android-studio webpage"
  exit 1
fi

echo "#!/bin/bash

## Download Android Studio from Google (needs wget)
wget -O /opt/android-studio-ide.zip '$dl'

## Compare SHA-256 Checksum (needs coreutils)
sha=\"\$(sha256sum /opt/android-studio-ide.zip)\"
if [ \"\$sha\" != \"$sha  /opt/android-studio-ide.zip\" ]; then
  echo 'SHA-256 Checksum mismatch, aborting installation'; rm -f /opt/android-studio-ide.zip; exit 1
fi" > "$TOP/android-studio/debian/preinst"

echo "Source: android-studio$suf
Section: devel
Priority: optional
Maintainer: Maarten Fonville <maarten.fonville@gmail.com>
Build-Depends: debhelper (>= 7.0.50~)
Standards-Version: 3.9.6
Homepage: http://developer.android.com/tools/studio/index.html


Package: android-studio$suf
Architecture: any
Suggests: default-jdk
Pre-Depends: wget, coreutils
Depends: \${misc:Depends}, java-sdk | oracle-java7-installer | oracle-java8-installer, unzip
Recommends: libc6-i386 [amd64], lib32stdc++6 [amd64], lib32gcc1 [amd64], lib32ncurses5 [amd64], lib32z1 [amd64]$trustydep
Conflicts: $con
Description: Android Studio.
 Android Studio is the official IDE for Android application development, based on IntelliJ IDEA." > "$TOP/android-studio/debian/control"


rm -f "$TOP/android-studio/debian/changelog"
pushd "$TOP/android-studio" > /dev/null
dch --create --force-distribution -v "$ver~$d" --package "android-studio$suf" -D "$d" -u low "Updated to $vername ($c)" #also possible to pass -M if you are the maintainer in the control file
popd > /dev/null
echo "android-studio${suf}_$ver~$d"
