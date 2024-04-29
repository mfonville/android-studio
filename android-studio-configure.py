#!/usr/bin/env python3

# requires, bs4, lxml
import argparse
import bs4
import os
import re
import requests
import shutil
import subprocess

session = requests.Session()
base_url = 'https://developer.android.com'

ENV = {'DEBFULLNAME': 'Maarten Fonville',
       'DEBEMAIL': 'maarten.fonville@gmail.com'}


class ReleasesManager(object):
    all_releases = {}

    def add_release(self, release):
        if release.major_version not in self.get_major_versions():
            self.all_releases[release.major_version] = []
        self.all_releases[release.major_version].append(release)

    def create_conflict_list(self, release):
        all_majors = self.get_major_versions()
        all_majors.remove(release.major_version)  # remove our self release serie
        result = ''
        for m in all_majors:
            result += (', android-studio-'+m)
        return result

    def get_latest_release(self, stable=False, majors=None):
        result = None
        if not majors:
            majors = self.get_major_versions()
        for m in majors:
            try:
                releases = self.all_releases[m]
            except KeyError:
                print('Major release series not found')
                return None
            for r in releases:
                if not result or r.is_newer_than(result.version_number):
                    if not stable or (stable and r.stable):
                        result = r
            if result:
                break
        return result

    def get_major_versions(self):
        return list(sorted(self.all_releases.keys(), key=lambda major: major.rjust(4, '.').rjust(8, '0'), reverse=True))  # fill old version number scheme with zeroes and a dot in front

    def retrieve_releases(self):
        try:
            response = session.get(base_url + '/studio/archive')
            page = bs4.BeautifulSoup(response.content, 'lxml')  # or html5lib
            iframe = page.find('devsite-iframe').iframe['src']

            if not iframe.startswith('http'):
                    iframe = base_url + iframe

            response = session.get(iframe)
            page = bs4.BeautifulSoup(response.content, 'lxml')  # or html5lib
            downloads = page.find_all('section', attrs={'class': 'expandable'})
            for download in downloads:
                stable = False
                if 'stable' in download['class']:
                    stable = True
                version_name = download.find('p', attrs={'class': 'expand-control'}).contents[0].split('\n')[0]
                if ' Patch ' in version_name:  # work around because newer "Patch" builds are not explicity marked as stable
                    stable = True
                match_old = re.search('Android Studio ([0-9]\\.[0-9]).*', version_name)
                match_interim = re.search('Android Studio ([0-9]{4}\\.[0-9]\\.[0-9]).*', version_name)
                match_new = re.search('Android Studio .* ([0-9]{4}\\.[0-9]\\.[0-9]).*', version_name)
                if match_old:
                    major_version = match_old.group(1)
                elif match_interim:
                    major_version = match_interim.group(1)
                elif match_new:
                    major_version = match_new.group(1)
                else:
                    continue  # skip this entry
                download_url_parse = download.find_all('a', attrs={'href': re.compile(r'.*-linux.tar.gz')})
                if download_url_parse:
                    download_url = download_url_parse[0]['href']
                else:
                    continue  # skip this entry
                match_old = re.search('.*/android-studio-ide-([0-9]*\\.[0-9]*)-linux.tar.gz', download_url)
                match_new = re.search('.*/android-studio-([0-9.]+)-linux.tar.gz', download_url)
                if match_old:
                    version_number = match_old.group(1)
                elif match_new:
                    version_number = match_new.group(1)
                else:
                    continue  # skip this entry
                match = re.search('.*([0-9a-f]{64}) (android-studio-(ide-)?[0-9.]+-linux\\.tar\\.gz)\\\\n.*', str(download.div.contents))
                if match:
                    sha256sum = match.group(1)
                    filename = match.group(2)
                else:
                    continue  # skip this entry
                self.add_release(AndroidStudioRelease(stable, major_version, version_name, version_number, download_url, sha256sum))
        except requests.exceptions.HTTPError as e:
            print('Error status {} fetching {}:\n{}'.format(e.response.status_code, e.response.url, e.response.content))


class AndroidStudioRelease(object):
    def __init__(self, stable, major_version, version_name, version_number, download_url, sha256sum):
        self.stable = stable
        self.major_version = major_version
        self.version_name = version_name
        self.version_number = version_number
        self.download_url = download_url
        self.sha256sum = sha256sum

    def is_newer_than(self, cmp_version_number):
        own_version_list = self.version_number.split('.')
        cmp_version_list = cmp_version_number.split('.')
        for i in range(0, len(own_version_list)):
            if i+1 > len(cmp_version_list):  # More sub-numbers in own_version wins
                return True
            if own_version_list[i] == cmp_version_list[i]:
                continue  # Go to next version number in the list
            elif int(own_version_list[i]) > int(cmp_version_list[i]):
                return True
            elif int(own_version_list[i]) < int(cmp_version_list[i]):
                return False
        return (len(own_version_list) > len(cmp_version_list))  # In all earlier version numbers were the same, then most sub-numbers in cmp_version wins

    def configure(self, distro, conflict_list, try_meta_package):
        try:
            if self.stable:
                shutil.copy('androidstudio-stable.svg', 'android-studio/androidstudio.svg')
            else:
                shutil.copy('androidstudio-preview.svg', 'android-studio/androidstudio.svg')

            with open('android-studio/android-studio.desktop', 'w+') as desktop:
                desktop.write('\
[Desktop Entry]\n\
Version=1.0\n\
Type=Application\n\
Terminal=false\n\
Name=Android Studio\n\
Exec=/opt/android-studio-{0}/android-studio/bin/studio.sh\n\
Comment=Integrated Android developer tools for development and debugging.\n\
Icon=androidstudio\n\
Categories=GNOME;GTK;Development;IDE;\n'.format(self.major_version))

            with open('android-studio/debian/android-studio-{0}.links'.format(self.major_version), 'w+') as packagelinks:
                packagelinks.write('\
opt/android-studio-{0}/android-studio opt/android-studio\n'.format(self.major_version))

            with open('android-studio/debian/postinst', 'w+') as postinst:
                postinst.write('\
#!/bin/bash\n\
\n\
## Only execute if preinst was succesful\n\
if [ -e /opt/android-studio-ide.tar.gz ]; then\n\
  ## Create a target directory for this major version\n\
  install -d "/opt/android-studio-{0}" -m "755"\n\
  ## Unpack Android Studio\n\
  tar -x -z -f /opt/android-studio-ide.tar.gz -C "/opt/android-studio-{0}"\n\
\n\
  ## Remove the package archive package at end\n\
  rm -f /opt/android-studio-ide.tar.gz\n\
\n\
  ## Give permissions to folder to let the built-in update system work\n\
  chmod ugo+rX -R "/opt/android-studio-{0}"\n\
\n\
  ## Make a symlink for flutter compatibility\n\
  ln -s "/opt/android-studio-{0}/android-studio/jbr" "/opt/android-studio-{0}/android-studio/jre"\n\
\n\
  ## Update icon caches\n\
  gtk-update-icon-cache /usr/share/icons/hicolor/\n\
  update-desktop-database -q\n\
  xdg-desktop-menu forceupdate\n\
  exit 0\n\
fi\n'.format(self.major_version))

            with open('android-studio/debian/postrm', 'w+') as postrm:
                postrm.write('\
#!/bin/bash\n\
\n\
## Remove the Android Studio folder\n\
rm -Rf /opt/android-studio-{0}/\n\
\n'.format(self.major_version))

            with open('android-studio/debian/preinst', 'w+') as preinst:
                preinst.write('\
#!/bin/bash\n\
\n\
## Download Android Studio from Google (needs wget)\n\
mkdir --mode=755 -p /opt\n\
wget -O /opt/android-studio-ide.tar.gz {0}\n\
\n\
## Compare SHA-256 Checksum (needs coreutils)\n\
sha="$(sha256sum /opt/android-studio-ide.tar.gz)"\n\
if [ "$sha" != "{1}  /opt/android-studio-ide.tar.gz" ]; then\n\
  echo "SHA-256 Checksum mismatch, aborting installation"; rm -f /opt/android-studio-ide.tar.gz; exit 1\n\
fi\n'.format(self.download_url, self.sha256sum))

            with open('android-studio/debian/control', 'w+') as control:
                control.write('\
Source: android-studio-{0}\n\
Section: devel\n\
Priority: optional\n\
Maintainer: Maarten Fonville <maarten.fonville@gmail.com>\n\
Build-Depends: debhelper (>= 7.0.50~)\n\
Standards-Version: 3.9.6\n\
Homepage: https://developer.android.com/tools/studio/index.html\n\
\n\
\n\
Package: android-studio-{0}\n\
Architecture: any\n\
Pre-Depends: wget, coreutils\n\
Depends: ${{misc:Depends}}, unzip\n\
Suggests: libc6-i386 [amd64], lib32z1 [amd64]\n\
Conflicts: android-studio-beta, android-studio-dev, android-studio-canary, android-studio-preview{1}\n\
Description: Android Studio\n\
 Android Studio is the official IDE for Android application development, based on IntelliJ IDEA.\n\
 \n'.format(self.major_version, conflict_list))
            if self.stable and try_meta_package:  # we only allow meta-package it is a release marked as stable
                with open('android-studio/debian/control', 'a+') as control:
                    control.write('\n\
Package: android-studio\n\
Depends: android-studio-{0}\n\
Architecture: any\n\
Description: Depends on the latest stable Android Studio\n\
\n'.format(self.major_version))

            if os.path.exists('android-studio/debian/changelog'):
                os.remove('android-studio/debian/changelog')

            subprocess.run(['dch',
                            '--create',
                            '--force-distribution',
                            '-v', self.version_number+'~'+distro+'+0',
                            '--package', 'android-studio-'+self.major_version,
                            '-D', distro,
                            '-u', 'low',
                            '"Updated to {}"'.format(self.version_name)],
                           cwd='android-studio/', env=ENV, check=True)
            print('android-studio-{}_{}~{}+0'.format(self.major_version, self.version_number, distro))
        except IOError as e:
            print('Error writing config files:\n{}'.format(e))
        except subprocess.CalledProcessError as e:
            print('Error executing dch:\n{}'.format(e))


if __name__ == "__main__":
    majors = None
    parser = argparse.ArgumentParser(prog='android-studio-configure')
    parser.add_argument('target', choices=['clean', 'focal', 'jammy', 'noble', 'oracular'], help='target distro release (or clean)')
    parser.add_argument('--stable', action='store_true', default=False, help='consider only stable releases')
    parser.add_argument('--metapackage', action='store_true', default=False, help='try to build meta package (if release is stable)')
    parser.add_argument('--major', help='limit to a specific major release serie')
    args = parser.parse_args()
    if args.target == 'clean':
        print('Cleaning configuration...')
        for f in ['android-studio/debian/control',
                  'android-studio/debian/changelog',
                  'android-studio/debian/changelog.dch',
                  'android-studio/debian/postinst',
                  'android-studio/debian/postrm',
                  'android-studio/debian/preinst',
                  'android-studio/androidstudio.svg',
                  'android-studio/android-studio.desktop']:
            if os.path.exists(f):
                os.remove(f)
        exit(0)

    if args.major:
        majors = [args.major]

    manager = ReleasesManager()
    manager.retrieve_releases()
    release = manager.get_latest_release(stable=args.stable, majors=majors)
    if release:
        release.configure(distro=args.target, conflict_list=manager.create_conflict_list(release), try_meta_package=args.metapackage)
