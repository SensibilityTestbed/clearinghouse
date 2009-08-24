"""
<Program>
  test_onepercentmanyevents_to_onepercentmanyevents.py

<Purpose>
  Test out the onepercentmanyevents_to_onepercentmanyevents transition state. 
  Test to see if the database is updated properly

<Authour>
  Monzur Muhammad
  monzum@cs.washington.edu

<Started>
  Aug 21, 2009
"""


# Warning: settings must be imported and the database values modified before
# anything else is imported. Failure to do this first will result in django
# trying to create a test mysql database.
from seattlegeni.website import settings

# Do not change the DATABASE_ENGINE. We want to be sure that sqlite3 is used
# for tests.
settings.DATABASE_ENGINE = 'sqlite3'
settings.TEST_DATABASE_NAME = 'test_seattlegeni'

import django.db
import django.test.utils

from seattlegeni.node_state_transitions import node_transition_lib
from seattlegeni.node_state_transitions import transition_onepercentmanyevents_to_onepercentmanyevents

from seattlegeni.common.api import maindb

from seattlegeni.node_state_transitions.tests import mockutil



#vessel dictionary for this test
vessels_dict = {}
vessels_dict[mockutil.extra_vessel_name] = {"userkeys" : [node_transition_lib.onepercentmanyeventspublickey],
                                   "ownerkey" : "SeattleGENI",
                                   "ownerinfo" : "",
                                   "status" : "",
                                   "advertise" : True}
vessels_dict["vessel_non_seattlegeni"] = {"userkeys" : ["some random key"],
                                   "ownerkey" : mockutil.donor_key,
                                   "ownerinfo" : "",
                                   "status" : "",
                                   "advertise" : True}
vessels_dict["random_vessel"] = {"userkeys" : ["some random key"],
                                   "ownerkey" : "random key",
                                   "ownerinfo" : "",
                                   "status" : "",
                                   "advertise" : True}








def setup_test():
  """
  <Purpose>
    Prepare everything in order to run the tests.

  <Arguments>
    None

  <Exceptions>
    None

  <Side Efects>
    None

  <Return>
    None
  """

  django.test.utils.setup_test_environment()

  # Creates a new test database and runs syncdb against it.
  django.db.connection.creation.create_test_db()

  # Create a user who has the donation key.
  user_object = maindb.create_user(mockutil.testusername, "password", "example@example.com", "affiliation", 
                    "10 11", "2 2 2", mockutil.donor_key_str)

  # Create a database entry for the node
  node_object = maindb.create_node(mockutil.nodeid_key_str, mockutil.node_ip, mockutil.node_port, "10.0test",
                                  True, mockutil.per_node_key_str, mockutil.extra_vessel_name)

  # Create a donation for user
  maindb.create_donation(node_object, user_object, "Making a donation")
  # Setup all the mock functions
  mockutil.mock_nodemanager_get_node_info(mockutil.nodeid_key, "10.0test", vessels_dict)
  mockutil.mock_lockserver_calls()
  mockutil.mock_backend_generate_key([mockutil.per_node_key_str])
  mockutil.mock_nodemanager_get_vesselresources()
  mockutil.mock_transitionlib_do_advertise_lookup([mockutil.node_address])
  mockutil.mock_backend_set_vessel_owner_key()
  mockutil.mock_backend_split_vessel()
  mockutil.mock_backend_set_vessel_user_keylist([mockutil._mock_pubkey_to_string(
                                                node_transition_lib.onepercentmanyeventspublickey)])
 



def run_database_update_test():
  """
  <Purpose>
    Run the test and make sure that the database was modified
    properly, the right keys were set, and generally all information
    is what was expected.

  <Arguments>
    None

  <Exceptions>
    None

  <Side Effects>
    None

  <Return>
    None
  """

  transitionlist = []

  active_nodes_list = maindb.get_active_nodes()
  active_nodes_list[0].is_active = False
  active_nodes_list[0].save()

  transitionlist.append((("startstatename", node_transition_lib.onepercentmanyeventspublickey),
                        ("endstatename", node_transition_lib.onepercentmanyeventspublickey),
                         transition_onepercentmanyevents_to_onepercentmanyevents.update_database,
                         node_transition_lib.noop,
                         transition_onepercentmanyevents_to_onepercentmanyevents.update_database_node))

  (success_count, failure_count) = node_transition_lib.do_one_processnode_run(transitionlist, "startstatename", 1)[0]

  assert(success_count == 1)
  assert(failure_count == 0)

  assert_database_info()

  assert(mockutil.set_vessel_owner_key_call_count == 0)
  assert(mockutil.set_vessel_user_keylist_call_count == 1)  





def assert_database_info():

  active_nodes_list = maindb.get_active_nodes()

  assert(len(active_nodes_list) == 1)
  assert(active_nodes_list[0].node_identifier == mockutil.nodeid_key_str)
  assert(active_nodes_list[0].last_known_ip == mockutil.node_ip)
  assert(active_nodes_list[0].last_known_port == mockutil.node_port)
  assert(active_nodes_list[0].extra_vessel_name == mockutil.extra_vessel_name)
  assert(active_nodes_list[0].owner_pubkey == mockutil.per_node_key_str)

  testuser = maindb.get_user(mockutil.testusername)
  donations_list = maindb.get_donations_by_user(testuser)

  assert(len(donations_list) == 1)
  assert(donations_list[0].node == active_nodes_list[0])





def teardown_test():

  # We aren't going to use any database again in this script, so we give django
  # an empty database name to restore as the value of settings.DATABASE_NAME.
  old_database_name = ''
  django.db.connection.creation.destroy_test_db(old_database_name)

  django.test.utils.teardown_test_environment()




if __name__ == "__main__":
  setup_test()
  try:
    run_database_update_test()
  finally:
    teardown_test()