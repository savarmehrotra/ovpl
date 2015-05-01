BUILD_DEST=build
CODE_DEST="${BUILD_DEST}/code"

all:  build 

init:
	mkdir -p ${BUILD_DEST}

build: init
	emacs  --script elisp/publish.el
	rm -f ${BUILD_DEST}/docs/*.html~

clean:
	rm -rf ${BUILD_DEST}

