import os
import constants as con
import pickle
import logging

def init_processing(processing_file_path, state):
    set_processing_state(processing_file_path, state)
    pickle.dump({"items":[],"sim_grades":[]}, open(processing_file_path, "wb"))

def set_processing_state(processing_file_path, state):
    state_path = "{0}.state".format(processing_file_path)
    with open(state_path, mode="w", encoding="utf-8") as state_out:
        state_out.write(" ".join(map(str,state)))

def get_processing_state(processing_file_path, default_state):
    state_path = "{0}.state".format(processing_file_path)
    if os.path.isfile(state_path):
        with open(state_path, mode="r", encoding="utf-8") as state_in:
            line = state_in.readline()
            return tuple(line.split())
    return default_state

def destroy_processing_state(processing_file_path):
    state_path = "{0}.state".format(processing_file_path)
    if os.path.isfile(state_path):
        os.remove(state_path)

def processing_state_exist(processing_file_path):
    state_path = "{0}.state".format(processing_file_path)
    return os.path.isfile(state_path)