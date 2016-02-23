#!/bin/bash
TOP="$(realpath .)"
export DEBFULLNAME="Maarten Fonville"
export DEBEMAIL="maarten.fonville@gmail.com"

case "$1" in
  trusty|wily|xenial) echo "Checking for new Android Studio release...";;
  clean) rm -f "$TOP/android-studio/debian/changelog" "$TOP/android-studio/debian/changelog.dch" "$TOP/android-studio/debian/preinst"; echo "Android Studio sources cleaned!"; exit 1;;
  *) echo "Unrecognized Ubuntu version, use a valid distribution as 1st argument"; exit 1;;
esac

href="$(wget -O - -q http://developer.android.com/sdk/index.html | grep -oE 'https://dl.google.com/dl/android/studio/ide-zips/.*-linux.zip')"
version="$(printf "$href" | sed -n 's/.*android-studio-ide-\([0-9\.]*\)-linux\.zip/\1/p')"
echo "Found Android Studio version $version"

if ! grep -q "$href" "$TOP/android-studio/debian/preinst" 2>/dev/null || ! grep -q "android-studio ($version~$1) $1" "$TOP/android-studio/debian/changelog" 2>/dev/null; then
  echo "#!/bin/bash

## Download Android Studio from Google
wget -O /opt/android-studio-ide.zip '$href'" > "$TOP/android-studio/debian/preinst"

  rm -f "$TOP/android-studio/debian/changelog"
  pushd "$TOP/android-studio" > /dev/null
  dch --create -v "$version~$1" --package android-studio -D "$1" -u low "Updated to Android Studio Linux $version" #also possible to pass -M if you are the maintainer in the control file
  popd > /dev/null
  echo "Updated sources to $version for $1"
else
  echo "Sources not updated"
fi
