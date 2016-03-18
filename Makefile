NAME := ursula-monitoring

# If we're on an --exact-match tag, use it as the package version,
# with iteration '1', stripping any leading 'v'. Otherwise, break
# the git describe output of 'TAG-NN-gSHORTREF' into version 'TAG'
# and iteration 'NN.gSHORTREF'. See git-describe(1).

ARCH      := all
VERSION   := $(shell (git describe --exact-match || git describe --abbrev=0) 2>/dev/null | sed 's/^v//')
ITERATION := $(shell git describe --exact-match &>/dev/null && echo 1 || git describe | perl -pe's/^[^-]+-//;s/-/./')
FPM_FLAGS := \
		-s dir -a $(ARCH) -p build \
		-v $(VERSION) --iteration $(ITERATION) \
		--license 'Apache 2.0' \
		--maintainer 'Blue Box, an IBM Company' \
		--vendor 'Blue Box, an IBM Company' \
		--url 'https://www.blueboxcloud.com/' \
		--description 'Sensu plugins for ursula monitoring'

all: build/$(NAME)-sensu_$(VERSION)-$(ITERATION)_$(ARCH).deb

build/$(NAME)-sensu_$(VERSION)-$(ITERATION)_$(ARCH).deb:
	fpm -t deb $(FPM_FLAGS) -d sensu -n $(NAME)-sensu --deb-no-default-config-files \
		sensu/plugins/=/etc/sensu/plugins

upload: repo_env all
	package_cloud upload $(PACKAGECLOUD_REPO)/ubuntu/trusty build/$(NAME)-sensu_$(VERSION)-$(ITERATION)_$(ARCH).deb

.PHONY: clean repo_env
clean:
	rm -f build/*

repo_env:
ifndef PACKAGECLOUD_REPO
	$(error PACKAGECLOUD_REPO not set in your environment)
endif
