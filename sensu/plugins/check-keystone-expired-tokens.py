#!/opt/openstack/current/keystone/bin/python
#
# Copyright 2015, Jesse Keating <jlk@bluebox.net>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import sys

from datetime import datetime

from keystone.cmd import cli
from keystone.common import environment
from keystone import token
from keystone.common import sql
from keystone.token.persistence.backends.sql import TokenModel
from keystone.token.persistence.backends.sql import Token

possible_topdir = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),
                                   os.pardir,
                                   os.pardir))
if os.path.exists(os.path.join(possible_topdir,
                               'keystone',
                               '__init__.py')):
    sys.path.insert(0, possible_topdir)

WATERMARK = 1000


def monkeypatch_method(cls):
    def decorator(func):
        setattr(cls, func.__name__, func)
        return func
    return decorator


@monkeypatch_method(Token)
def list_tokens(self):
    now = datetime.utcnow()
    with sql.session_for_read() as session:
        query = session.query(TokenModel)
        tokens = query.filter(TokenModel.expires < now).count()
        if tokens > WATERMARK:
            print("expired tokens not being flushed."
                  " current count: %s" % tokens)
            sys.exit(1)


class TokenList(cli.BaseApp):
    """List tokens in the DB. This class is added to
       keystone-manage at runtime, and provides 'token_list' """

    name = "token_list"

    @classmethod
    def main(cls):
        token_manager = token.persistence.PersistenceManager()
        token_manager.driver.list_tokens()

cli.CMDS.append(TokenList)


if __name__ == '__main__':
    environment.use_stdlib()

    dev_conf = os.path.join(possible_topdir,
                            'etc',
                            'keystone.conf')
    config_files = None
    if os.path.exists(dev_conf):
        config_files = [dev_conf]

    # keystone-manage wants a command as a argv, so give it token_list
    sys.argv.append('token_list')
    cli.main(argv=sys.argv, config_files=config_files)
