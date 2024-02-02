FROM ubuntu:trusty

RUN apt-get update && apt-get install -y tar curl git
RUN apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev

RUN git clone https://github.com/yyuu/pyenv.git /root/.pyenv \
    && echo 'eval "$(pyenv init -)"' >> /root/.bash_profile

ENV PYENV_ROOT /root/.pyenv
ENV PATH $PYENV_ROOT/bin:/pyenv/venv/bin:$PATH

RUN mkdir /pyenv
WORKDIR /pyenv

ADD .python-version .python-version
ADD requirements.txt requirements.txt
ADD dev-requirements.txt dev-requirements.txt

RUN . ~/.bash_profile \
    && pyenv install --skip-existing \
    && pyenv rehash \
    && pip install virtualenv \
    && ([ -d venv ] || virtualenv venv) \
    && . venv/bin/activate \
    && pip install -r requirements.txt \
    && pip install -r dev-requirements.txt

RUN mkdir /reppy
WORKDIR /reppy

ADD . .

RUN git submodule update --init --recursive

CMD make test

