FROM ubuntu:trusty
RUN apt-get update -yy && \
    apt-get install -yy ruby ruby-dev build-essential git && \
    git clone https://github.com/jordansissel/fpm.git && \
    cd fpm && gem install --no-ri --no-rdoc fpm
WORKDIR /ursula-monitoring
CMD make
