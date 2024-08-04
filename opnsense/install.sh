#!/usr/bin/env sh

DIR=$(cd `dirname $0` && pwd)

# Install action
ln -Fs ${DIR}/actions_antiz.conf /usr/local/opnsense/service/conf/actions.d/actions_antiz.conf

# Reload config daemon
service configd restart

# Initially fetch data file
${DIR}/../doall.sh 
