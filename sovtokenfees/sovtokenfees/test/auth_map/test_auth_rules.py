import json
import sys
from typing import NamedTuple, Dict

import pytest
from indy.did import replace_keys_start
from indy_common.authorize.auth_constraints import AuthConstraint, ROLE, AuthConstraintOr, AbstractAuthConstraint, \
    IDENTITY_OWNER, AuthConstraintAnd

from indy_node.test.auth_rule.helper import sdk_send_and_check_auth_rule_request

from indy_common.constants import NYM, TRUST_ANCHOR, NODE, POOL_UPGRADE, POOL_RESTART, VALIDATOR_INFO, GET_SCHEMA

from indy_common.authorize.auth_actions import EDIT_PREFIX, ADD_PREFIX
from sovtoken.constants import AMOUNT, ADDRESS
from sovtokenfees.constants import FEES, FEES_FIELD_NAME
from sovtokenfees.test.helper import add_fees_request_with_address

from plenum.common.constants import TRUSTEE, STEWARD, STEWARD_STRING, TRUSTEE_STRING, VERKEY
from plenum.common.exceptions import RequestRejectedException
from plenum.test.helper import sdk_multisign_request_object, sdk_multi_sign_request_objects
from plenum.test.pool_transactions.helper import sdk_add_new_nym

auth_constraint = AuthConstraint(role=TRUSTEE, sig_count=1, need_to_be_owner=False)

# fee_1 = ("fee_1", 1)
# fee_2 = ("fee_2", 2)
# fee_3 = ("fee_3", 3)
# fee_5 = ("fee_5", 5)
# fee_6 = ("fee_6", 6)
# fee_100 = ("fee_100", 100)
fee_1 = (NODE, 1)
fee_2 = (POOL_UPGRADE, 2)
fee_3 = (POOL_RESTART, 3)
fee_5 = (NYM, 5)
fee_6 = (VALIDATOR_INFO, 6)
fee_100 = (GET_SCHEMA, 100)

set_fees = dict([
    fee_1,
    fee_2,
    fee_3,
    fee_5,
    fee_6,
    fee_100
])

RequestParams = NamedTuple("RequestParams", [("fees", int),
                                             ("owner", str),
                                             ("wallets", Dict[str, int])]
                           )
RequestParams.__new__.__defaults__ = (0, None, {})

InputParam = NamedTuple("InputParam", [
    ("auth_constraint", AbstractAuthConstraint),
    ("valid_requests", [RequestParams]),
    ("invalid_requests", [RequestParams])])

steward_address = ""
trustee_address = ""
owner_address = ""

input_params_map = [
    InputParam(auth_constraint=AuthConstraintOr([AuthConstraint(STEWARD, 1,
                                                                metadata={FEES_FIELD_NAME: fee_5[0]}),
                                                 AuthConstraint(TRUSTEE, 1)]),
               valid_requests=[
                   RequestParams(fees=fee_5[1],
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=0,
                                 wallets={TRUSTEE: 1}),
                   RequestParams(fees=fee_5[1],
                                 wallets={TRUSTEE: 1,
                                          STEWARD: 1}),
               ],
               invalid_requests=[
                   RequestParams(fees=fee_1[1],
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=fee_5[1],
                                 wallets={TRUSTEE: 1}),
                   RequestParams(fees=fee_5[1],
                                 wallets={IDENTITY_OWNER: 1})
               ]),
    InputParam(auth_constraint=AuthConstraintAnd([AuthConstraint(STEWARD, 2),
                                                  AuthConstraint(TRUSTEE, 1,
                                                                 metadata={FEES_FIELD_NAME: fee_5[0]})]),
               valid_requests=[
                   RequestParams(fees=fee_5[1],
                                 wallets={STEWARD: 2,
                                          TRUSTEE: 1}),
                   RequestParams(fees=fee_5[1],
                                 wallets={STEWARD: 3,
                                          TRUSTEE: 2}),
               ],
               invalid_requests=[
                   RequestParams(fees=fee_5[1],
                                 wallets={STEWARD: 3}),
                   RequestParams(fees=fee_5[1],
                                 wallets={TRUSTEE: 3}),
                   RequestParams(fees=fee_5[1],
                                 wallets={STEWARD: 1,
                                          TRUSTEE: 1})
               ]),
    InputParam(auth_constraint=AuthConstraintOr([AuthConstraint(STEWARD, 1,
                                                                metadata={FEES_FIELD_NAME: fee_2[0]}),
                                                 AuthConstraint(STEWARD, 1,
                                                                metadata={FEES_FIELD_NAME: fee_5[0]})]),
               valid_requests=[
                   RequestParams(fees=fee_5[1],
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=fee_2[1],
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=fee_2[1],
                                 wallets={STEWARD: 1,
                                          TRUSTEE: 1}),
               ],
               invalid_requests=[
                   RequestParams(fees=fee_6[1],
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=fee_5[1],
                                 wallets={TRUSTEE: 1})
               ]),
    InputParam(auth_constraint=AuthConstraintOr([AuthConstraint(STEWARD, 3,
                                                                metadata={FEES_FIELD_NAME: fee_1[0]}),
                                                 AuthConstraint(TRUSTEE, 1,
                                                                metadata={FEES_FIELD_NAME: fee_2[0]}),
                                                 AuthConstraint(IDENTITY_OWNER, 1,
                                                                metadata={FEES_FIELD_NAME: fee_100[0]}),
                                                 ]),
               valid_requests=[
                   RequestParams(fees=fee_1[1],
                                 wallets={STEWARD: 3}),
                   RequestParams(fees=0,
                                 wallets={TRUSTEE: 2}),
                   RequestParams(fees=fee_100[1],
                                 wallets={IDENTITY_OWNER: 1}),
                   RequestParams(fees=fee_100[1],
                                 wallets={STEWARD: 3,
                                          TRUSTEE: 1,
                                          IDENTITY_OWNER: 1}),
               ],
               invalid_requests=[
                   RequestParams(fees=fee_1[1],
                                 wallets={STEWARD: 2}),
                   RequestParams(fees=fee_100[1],
                                 wallets={TRUSTEE: 1})
               ]),
    InputParam(auth_constraint=AuthConstraintOr([AuthConstraint(STEWARD, 3,
                                                                metadata={FEES_FIELD_NAME: fee_1[0]}),
                                                 AuthConstraintAnd([
                                                     AuthConstraint(TRUSTEE, 1),
                                                     AuthConstraint(STEWARD, 1)])
                                                 ]),
               valid_requests=[
                   RequestParams(fees=fee_1[1],
                                 wallets={STEWARD: 1,
                                          TRUSTEE: 1}),
                   RequestParams(fees=fee_1[1],
                                 wallets={TRUSTEE: 1}),
                   RequestParams(fees=0,
                                 wallets={STEWARD: 1,
                                          TRUSTEE: 1})
               ],
               invalid_requests=[
                   RequestParams(fees=0,
                                 wallets={TRUSTEE: 1}),
                   RequestParams(fees=fee_1[1],
                                 wallets={STEWARD: 1})
               ]),
    InputParam(auth_constraint=AuthConstraintOr([AuthConstraint(STEWARD, 1,
                                                                need_to_be_owner=False,
                                                                metadata={FEES_FIELD_NAME: fee_3[0]}),
                                                 AuthConstraint(STEWARD, 1,
                                                                need_to_be_owner=True,
                                                                metadata={FEES_FIELD_NAME: fee_1[0]})
                                                 ]),
               valid_requests=[
                   RequestParams(fees=fee_3[1],
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=fee_1[1],
                                 owner=STEWARD,
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=fee_3[1],
                                 owner=STEWARD,
                                 wallets={STEWARD: 2})
               ],
               invalid_requests=[
                   RequestParams(fees=0,
                                 owner=STEWARD,
                                 wallets={STEWARD: 2}),
                   RequestParams(fees=fee_1[1],
                                 wallets={STEWARD: 1})
               ]),
    InputParam(auth_constraint=AuthConstraintAnd([AuthConstraint(STEWARD, 1,
                                                                 need_to_be_owner=False,
                                                                 metadata={FEES_FIELD_NAME: fee_3[0]}),
                                                  AuthConstraint(STEWARD, 1,
                                                                 need_to_be_owner=True)
                                                  ]),
               valid_requests=[
                   RequestParams(fees=fee_3[1],
                                 owner=STEWARD,
                                 wallets={STEWARD: 2})
               ],
               invalid_requests=[
                   RequestParams(fees=fee_3[1],
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=fee_1[1],
                                 owner=STEWARD,
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=0,
                                 wallets={TRUSTEE: 1}),
                   RequestParams(fees=0,
                                 owner=STEWARD,
                                 wallets={STEWARD: 2})
               ]),
    InputParam(auth_constraint=AuthConstraintOr([AuthConstraint("*", 1,
                                                                metadata={FEES_FIELD_NAME: fee_5[0]}),
                                                 AuthConstraint(TRUSTEE, 1),
                                                 AuthConstraint(STEWARD, 1),
                                                 AuthConstraint(TRUST_ANCHOR, 1),
                                                 ]),
               valid_requests=[
                   RequestParams(fees=0,
                                 wallets={TRUSTEE: 1}),
                   RequestParams(fees=0,
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=0,
                                 wallets={TRUST_ANCHOR: 1}),
                   RequestParams(fees=fee_5[1],
                                 wallets={IDENTITY_OWNER: 1}),
                   RequestParams(fees=0,
                                 wallets={IDENTITY_OWNER: 1,
                                          TRUSTEE: 1})
               ],
               invalid_requests=[
                   RequestParams(fees=fee_5[1],
                                 wallets={TRUSTEE: 1}),
                   RequestParams(fees=fee_1[1],
                                 wallets={IDENTITY_OWNER: 1}),
                   RequestParams(fees=0,
                                 wallets={IDENTITY_OWNER: 1})
               ]),
    InputParam(auth_constraint=AuthConstraint(TRUSTEE, 3),
               valid_requests=[
                   RequestParams(fees=0,
                                 wallets={TRUSTEE: 3}),
                   RequestParams(fees=0,
                                 wallets={TRUSTEE: 4})
               ],
               invalid_requests=[
                   RequestParams(fees=fee_1[1],
                                 wallets={TRUSTEE: 3}),
                   RequestParams(fees=0,
                                 wallets={TRUSTEE: 1}),
                   RequestParams(fees=0,
                                 wallets={STEWARD: 3})
               ]),
    InputParam(auth_constraint=AuthConstraint(TRUSTEE, 1),
               valid_requests=[
                   RequestParams(fees=0,
                                 wallets={TRUSTEE: 1}),
                   RequestParams(fees=0,
                                 wallets={TRUSTEE: 2})
               ],
               invalid_requests=[
                   RequestParams(fees=0,
                                 wallets={IDENTITY_OWNER: 1})
               ]),
    InputParam(auth_constraint=AuthConstraint("*", 1,
                                              need_to_be_owner=True,
                                              metadata={FEES_FIELD_NAME: fee_1[0]}),
               valid_requests=[
                   RequestParams(fees=fee_1[1],
                                 owner=IDENTITY_OWNER,
                                 wallets={IDENTITY_OWNER: 1}),
                   RequestParams(fees=fee_1[1],
                                 owner={IDENTITY_OWNER: 1},
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=fee_1[1],
                                 owner=STEWARD,
                                 wallets={TRUSTEE: 1,
                                          STEWARD: 1})
               ],
               invalid_requests=[
                   RequestParams(fees=fee_1[1],
                                 wallets={STEWARD: 1})
               ]),
    InputParam(auth_constraint=AuthConstraintOr([AuthConstraint(TRUSTEE, 3),
                                                 AuthConstraint(STEWARD, 1,
                                                                need_to_be_owner=False),
                                                 ]),
               valid_requests=[
                   RequestParams(fees=0,
                                 wallets={TRUSTEE: 3}),
                   RequestParams(fees=0,
                                 owner=TRUSTEE,
                                 wallets={TRUSTEE: 3}),
                   RequestParams(fees=0,
                                 owner=STEWARD,
                                 wallets={STEWARD: 1})
               ],
               invalid_requests=[
                   RequestParams(fees=0,
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=0,
                                 wallets={TRUSTEE: 2})
               ]),
    InputParam(auth_constraint=AuthConstraintOr([AuthConstraint(STEWARD, 1,
                                                                metadata={FEES_FIELD_NAME: fee_5[0]}),
                                                 AuthConstraint(STEWARD, 2),
                                                 ]),
               valid_requests=[
                   RequestParams(fees=fee_5[1],
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=0,
                                 wallets={STEWARD: 2})
               ],
               invalid_requests=[
                   RequestParams(fees=fee_5[1],
                                 wallets={STEWARD: 2}),
                   RequestParams(fees=0,
                                 wallets={STEWARD: 1})
               ]),
    InputParam(auth_constraint=AuthConstraintOr([AuthConstraint(STEWARD, 1,
                                                                metadata={FEES_FIELD_NAME: fee_5[0]}),
                                                 AuthConstraint(STEWARD, 1),
                                                 ]),
               valid_requests=[
                   RequestParams(fees=fee_5[1],
                                 wallets={STEWARD: 1}),
                   RequestParams(fees=0,
                                 wallets={STEWARD: 1})
               ],
               invalid_requests=[
                   RequestParams(fees=0,
                                 wallets={IDENTITY_OWNER: 2})
               ]),
]


@pytest.fixture(params=input_params_map)
def input_param(request):
    return request.param


@pytest.fixture()
def mint_tokens(helpers, address):
    outputs = [{ADDRESS: address, AMOUNT: 1000}]
    return helpers.general.do_mint(outputs)


@pytest.fixture(scope='module')
def sdk_wallet_stewards(looper,
                        sdk_wallet_trustee,
                        sdk_pool_handle):
    sdk_wallet_stewards = []
    for i in range(3):
        wallet = sdk_add_new_nym(looper,
                                 sdk_pool_handle,
                                 sdk_wallet_trustee,
                                 alias='steward{}'.format(i),
                                 role=STEWARD_STRING)
        sdk_wallet_stewards.append(wallet)
    return sdk_wallet_stewards


@pytest.fixture(scope='module')
def sdk_wallet_clients(looper,
                       sdk_wallet_trustee,
                       sdk_pool_handle):
    sdk_wallet_clients = []
    for i in range(3):
        wallet = sdk_add_new_nym(looper,
                                 sdk_pool_handle,
                                 sdk_wallet_trustee,
                                 alias='client{}'.format(i))
        sdk_wallet_clients.append(wallet)
    return sdk_wallet_clients


@pytest.fixture(scope='module')
def sdk_wallet_trustees(looper,
                        sdk_wallet_trustee,
                        sdk_pool_handle):
    sdk_wallet_trustees = []
    for i in range(3):
        wallet = sdk_add_new_nym(looper,
                                 sdk_pool_handle,
                                 sdk_wallet_trustee,
                                 alias='trustee{}'.format(i),
                                 role=TRUSTEE_STRING)
        sdk_wallet_trustees.append(wallet)
    return sdk_wallet_trustees


@pytest.fixture()
def address(helpers):
    # addresses = {}
    # address = [helpers.wallet.create_address()
    # for wallet in [sdk_wallet_trustees + \
    #                sdk_wallet_stewards + \
    #                sdk_wallet_clients]:
    #     address = helpers.wallet.create_address(wallet)
    #     addresses[wallet.identifiers[0]] = address
    return helpers.wallet.create_address()


def add_fees_request_with_address(helpers, fee_amount, request, address):
    utxos_found = helpers.general.get_utxo_addresses([address])[0]
    request_with_fees = helpers.request.add_fees(
        request,
        utxos_found,
        fee_amount,
        change_address=address
    )[0]
    request_with_fees = json.loads(request_with_fees)
    setattr(request, FEES, request_with_fees[FEES])
    return request


def _send_request(looper, helpers, fees, wallets_count, address, owner, sdk_wallet_trustee,
                  sdk_wallet_trustees, sdk_wallet_stewards, sdk_wallet_clients):
    wallets = sdk_wallet_trustees[:wallets_count.get(TRUSTEE, 0)] + \
              sdk_wallet_stewards[:wallets_count.get(STEWARD, 0)] + \
              sdk_wallet_clients[:wallets_count.get(IDENTITY_OWNER, 0)]
    # create request
    wh, dest = sdk_wallet_trustee
    if owner == TRUSTEE:
        wh, dest = sdk_wallet_trustees[0]
    elif owner == STEWARD:
        wh, dest = sdk_wallet_stewards[0]
    elif owner == IDENTITY_OWNER:
        wh, dest = sdk_wallet_clients[0]

    verkey = looper.loop.run_until_complete(
        replace_keys_start(wh, dest, json.dumps({})))
    client_request = helpers.request.nym(sdk_wallet=wallets[0], dest=dest, verkey=verkey)
    client_request.signature = None
    client_request.signatures = None
    # add fees
    client_request = add_fees_request_with_address(helpers,
                                                   fees,
                                                   client_request,
                                                   address)
    # sign request
    client_request = sdk_multi_sign_request_objects(looper, wallets, [client_request])

    return helpers.sdk.sdk_send_and_check(client_request)


def test_authorization(looper, mint_tokens, sdk_wallet_trustee,
                       sdk_pool_handle, helpers, input_param, address,
                       sdk_wallet_trustees, sdk_wallet_stewards, sdk_wallet_clients):
    helpers.general.do_set_fees(set_fees)
    sdk_send_and_check_auth_rule_request(looper, sdk_wallet_trustee,
                                         sdk_pool_handle, auth_action=EDIT_PREFIX,
                                         auth_type=NYM, field=VERKEY, new_value="*", old_value="*",
                                         constraint=input_param.auth_constraint.as_dict)
    for req in input_param.valid_requests:
        _send_request(looper, helpers, req.fees, req.wallets, address,
                      req.owner, sdk_wallet_trustee,
                      sdk_wallet_trustees, sdk_wallet_stewards, sdk_wallet_clients)

    for req in input_param.invalid_requests:
        with pytest.raises(RequestRejectedException, match="UnauthorizedClientRequest"):
            _send_request(looper, helpers, req.fees, req.wallets, address,
                          req.owner, sdk_wallet_trustee,
                          sdk_wallet_trustees, sdk_wallet_stewards, sdk_wallet_clients)