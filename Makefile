NAME := ursula-monitoring

# If we're on an --exact-match tag, use it as the package version,
# with iteration '1', stripping any leading 'v'. Otherwise, break
# the git describe output of 'TAG-NN-gSHORTREF' into version 'TAG'
# and iteration 'NN.gSHORTREF'. See git-describe(1).

VERSION   := $(shell (git describe --exact-match || git describe --abbrev=0) 2>/dev/null | sed 's/^v//')
ITERATION := $(shell git describe --exact-match &>/dev/null && echo 1 || git describe | perl -pe's/^[^-]+-//;s/-/./')
FPM_FLAGS := \
		-s dir -a all -p build \
		-v $(VERSION) --iteration $(ITERATION) \
		--license 'Apache 2.0' \
		--maintainer 'Blue Box, an IBM Company' \
		--vendor 'Blue Box, an IBM Company' \
		--url 'https://www.blueboxcloud.com/' \
		--description 'Sensu plugins for ursula monitoring'

.PHONY: sensu_deb sensu_rpm collectd_deb collectd_rpm all clean

all: sensu_deb sensu_rpm collectd_deb collectd_rpm

sensu_rpm:
	fpm -t rpm $(FPM_FLAGS) -d sensu -n $(NAME)-sensu \
		sensu/plugins/=/etc/sensu/plugins

sensu_deb:
	fpm -t deb $(FPM_FLAGS) -d sensu -n $(NAME)-sensu \
		sensu/plugins/=/etc/sensu/plugins

clean:
	rm -f build/*
