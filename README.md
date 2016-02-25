Android Studio for Ubuntu
=====================

Android Studio by Google packaged for Ubuntu

Visit the official website [here](http://mfonville.github.io/android-studio)

Based upon the work of @PaoloRotolo

##FAQ
##### Unable to start
**Q:** *When I click on the icon, Android Studio just doesn't start.*
**A:** Did you install Java? Try to install Java 8 from [this PPA](http://www.webupd8.org/2012/09/install-oracle-java-8-in-ubuntu-via-ppa.html).

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

##### HiDPI support
**Q:** *Android Studio looks strange. Some icons and objects are way too small.*

**A:** You need to use the Android Studio (HiDPI) version on your high resolution screen.
