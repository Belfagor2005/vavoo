SUMMARY = "Lululla"
MAINTAINER = "Lululla"
SECTION = "base"
PRIORITY = "required"
LICENSE = "proprietary"

require conf/license/license-gplv2.inc

RDEPENDS:${PN} = "ffmpeg gstplayer exteplayer3 enigma2-plugin-systemplugins-serviceapp"

inherit allarch gitpkgv python3-compileall

PV = "1.0+git${SRCPV}"
PKGV = "1.0+git${GITPKGV}"
VER ="1.0"
PR = "r0"

SRC_URI = "git://github.com/Belfagor2005/vavoo.git;protocol=https;branch=main"

S = "${WORKDIR}/git"

FILES:${PN} = "/usr/*"
FILES:${PN}-src = "${libdir}/enigma2/python/Plugins/Extensions/vavoo/*.py ${libdir}/enigma2/python/Plugins/Extensions/vavoo/*/*.py"

do_install() {
    cp -af --no-preserve=ownership ${S}/usr* ${D}/
}
