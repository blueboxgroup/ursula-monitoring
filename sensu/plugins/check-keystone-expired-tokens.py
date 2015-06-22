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

possible_topdir = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),
                                   os.pardir,
                                   os.pardir))
if os.path.exists(os.path.join(possible_topdir,
                               'keystone',
                               '__init__.py')):
    sys.path.insert(0, possible_topdir)

from keystone import cli
from keystone.common import environment
from keystone import token
from keystone.common import sql
from oslo.utils import timeutils

WATERMARK=1000

# Monkeypatch the sql Token class to add a method
from keystone.token.persistence.backends.sql import TokenModel
from keystone.token.persistence.backends.sql import Token

def monkeypatch_method(cls):
    def decorator(func):
        setattr(cls, func.__name__, func)
        return func
    return decorator

@monkeypatch_method(Token)
def list_tokens(self):
    session = sql.get_session()
    with session.begin():
        now = timeutils.utcnow()
        query = session.query(TokenModel)
        query = query.filter(TokenModel.expires < now)
        tokens = query.all()
    if len(tokens) > WATERMARK:
        print("Too many expired keystone tokens: %s" % len(tokens))
        sys.exit(1)

# Create a class for listing the tokens and add it to the keystone-manage
# command list
class TokenList(cli.BaseApp):
    """List tokens in the DB"""

    name = "token_list"

    @classmethod
    def main(cls):
        token_manager = token.persistence.PersistenceManager()
        token_manager.driver.list_tokens()

cli.CMDS.append(TokenList)

# Now do our thing
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
