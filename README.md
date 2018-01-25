Android Studio for Ubuntu
=====================

Android Studio by Google packaged for Ubuntu

Visit the official website [here](http://mfonville.github.io/android-studio)

Based upon the work of @PaoloRotolo

## How-to

#### Install android-studio
Download pre-built packages from our [PPA](https://launchpad.net/~maarten-fonville/+archive/ubuntu/android-studio)

#### Build android-studio
Run configure with the parameters for the package you want to build:
```
./configure (trusty|xenial|artful|bionic) (stable|preview)
```
E.g. if you want to make a package of stable for bionic:
```
./configure bionic stable
```
After configuring you can build the package as usual with `debuild` or `pbuilder` in the *android-studio* folder

## FAQ

##### Unable to start
**Q:** *When I click on the icon, Android Studio just doesn't start.*

**A:** Did you install Java? Try to install [Java Development Kit](http://packages.ubuntu.com/default-jdk) with `sudo apt install default-jdk`.

Also, try:
```
/opt/android-studio/bin/studio.sh
```
If you have this error, you probably have to install the **jdk**:
```
Start Failed: Internal error. Please report to https://code.google.com/p/android/issues

java.lang.NoClassDefFoundError: com.intellij.util.lang.ClassPath
at java.lang.Class.initializeClass(libgcj.so.14)
[...]
```
