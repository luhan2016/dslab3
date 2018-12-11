# coding=utf-8
# ------------------------------------------------------------------------------------------------------
# TDA596 - Lab 1
# server/server.py
# Input: Node_ID total_number_of_ID
# Student: John Doe
# ------------------------------------------------------------------------------------------------------
import traceback
import sys
import time
import json
import argparse
from threading import Thread
import threading

from bottle import Bottle, run, request, template
import requests
import operator

# ------------------------------------------------------------------------------------------------------
try:
    app = Bottle()

    board = {0:"nothing,lc,ts,node_id"} 
    new_board = {0:"nothing,lc,ts,node_id"} 
    lock = threading.Lock()
    # ------------------------------------------------------------------------------------------------------
    # BOARD FUNCTIONS
    # ------------------------------------------------------------------------------------------------------
    def add_new_element_to_store(entry_sequence, element, precede_vessel_id, logical_clock,time_stamp, is_propagated_call = False):
        global board
        success = False
        lock.acquire()
        try:
            board[entry_sequence] = "{},{},{},{}".format(element,precede_vessel_id, logical_clock, time_stamp)
            million_seconds = int(round(time.time()*1000))
            print "\n\nelement is {},precede_vessel_id is {}, logical_clock is {}, time_stamp is{},million_seconds is {}\n\n".format(element,precede_vessel_id, logical_clock, time_stamp,million_seconds)
            success = True
            t = Thread(target=eventually_consistency) 
            t.daemon = True
            t.start()
        except Exception as e:
            print e
        lock.release()
        return success

    def modify_element_in_store(entry_sequence, element, precede_vessel_id, logical_clock,time_stamp, is_propagated_call = False):
        global board, node_id
        success = False
        lock.acquire()
        try:
            if is_propagated_call == False:
                board[entry_sequence] = "{},{},{},{}".format(element,precede_vessel_id, logical_clock, time_stamp)
                success = True
            else:
                for key, value in board.items():
                    en,pre_id,lc,ts = value.split(',')
                    if int(precede_vessel_id) == int(pre_id) and int(time_stamp) == int(ts):
                        board[entry_sequence] = "{},{},{},{}".format(element,precede_vessel_id, logical_clock, time_stamp)
                        success = True
        except Exception as e:
            print e
        lock.release()
        if success == True:
            return success
        else:
            t = Thread(target=modify_element_in_store,args=(entry_sequence, element, precede_vessel_id, logical_clock,time_stamp, is_propagated_call)) 
            t.daemon = True
            t.start()

    def delete_element_from_store(entry_sequence, precede_vessel_id, logical_clock, time_stamp, is_propagated_call = False):
        global board, node_id
        success = False
        lock.acquire()
        try:
            if is_propagated_call == False:
                board.pop(entry_sequence)  
                new_board.pop(entry_sequence)
                success = True
            else:
                for key, value in board.items():
                    en,pre_id,lc,ts = value.split(',')
                    if int(precede_vessel_id) == int(pre_id) and int(time_stamp) == int(ts):
                        board.pop(key)  
                        new_board.pop(key)
                        success = True
        except Exception as e:
            print e
        lock.release()
        if success == True:
            return success
        else:
            t = Thread(target=delete_element_from_store,args=(entry_sequence, precede_vessel_id, logical_clock, time_stamp, is_propagated_call)) 
            t.daemon = True
            t.start()

    # ------------------------------------------------------------------------------------------------------
    # DISTRIBUTED COMMUNICATIONS FUNCTIONS
    # ------------------------------------------------------------------------------------------------------
    def contact_vessel(vessel_ip, path, payload=None, req='POST'):
        # Try to contact another server (vessel) through a POST or GET, once
        success = False
        try:
            if 'POST' in req:
                res = requests.post('http://{}{}'.format(vessel_ip, path), data=payload)
            elif 'GET' in req:
                res = requests.get('http://{}{}'.format(vessel_ip, path))
            else:
                print 'Non implemented feature!'
            # result is in res.text or res.json()
            #print(res.text)
            if res.status_code == 200:
                success = True
        except Exception as e:
            print e
        return success

    def propagate_to_vessels(path, payload = None, req = 'POST'):
        global vessel_list, node_id
        for vessel_id, vessel_ip in vessel_list.items():
            if int(vessel_id) != node_id: # don't propagate to yourself
                success = contact_vessel(vessel_ip, path, payload, req)
                #if not success:
                    #print "\n\nCould not contact vessel {}\n\n".format(vessel_id)

    def eventually_consistency():
        global board
        print "\ndoing eventually consistency..."
        for key1, value1 in board.items():
            en1,pre_id1,lc1,ts1 = value1.split(',')
            for key2,value2 in board.items():
                en2,pre_id2,lc2,ts2 = value2.split(',')
                if key1 < key2: # compare with the next entry in the board dictionary
                    if ts1 > ts2: # small timestamp should display first in the webpage, so swap the value
                        temp = board[key1]
                        board[key1] = board[key2]
                        board[key2] = temp
                    elif ts1 == ts2: # timestamp is the same, break the tie with increase node_id order 
                        if pre_id1 > pre_id2: # vessel with small node id should dispaly first
                            temp = board[key1]
                            board[key1] = board[key2]
                            board[key2] = temp
        million_seconds = int(round(time.time()*1000))
        print "\nfinish eventually consistency!"
        print "million_seconds is {}\n".format(million_seconds)

    # ------------------------------------------------------------------------------------------------------
    # ROUTES
    # ------------------------------------------------------------------------------------------------------
    # a single example (index) should be done for get, and one for post
    # ------------------------------------------------------------------------------------------------------
    @app.route('/')
    def index():
        global board, node_id,new_board
        for key, value in board.items():
            en,lc,ts,no_id = value.split(',')
            new_board[key] = en
        return template('server/index.tpl', board_title='Vessel {}'.format(node_id), board_dict=sorted(new_board.iteritems()), \
                                            members_name_string='lhan@student.chalmers.se;shahn@student.chalmers.se')

    @app.get('/board')
    def get_board():
        global board, node_id,new_board
        for key, value in board.items():
            en,lc,ts,no_id = value.split(',')
            new_board[key] = en
            #print en  #no input, print nothing, en is entry value
        return template('server/boardcontents_template.tpl',board_title='Vessel {}'.format(node_id), board_dict=sorted(new_board.iteritems()))
    # ------------------------------------------------------------------------------------------------------
    @app.post('/board')
    def client_add_received():
        '''Adds a new element to the board, Called directly when a user is doing a POST request on /board'''
        global board, node_id, sequence_number,LC,TS
        try:
            new_entry = request.forms.get('entry') # new_entry is the user input from webpage, Change board value from nothing to new_entry
            # propagate threads to avoid blocking,create the thread as a deamon
            LC = LC + 1
            TS = LC
            #print "\nLC:{},TS:{}\n".format(LC,TS)
            add_new_element_to_store(sequence_number, new_entry, node_id, LC, TS) 
            board_dict = {sequence_number : new_entry}
            t = Thread(target=propagate_to_vessels, args = ('/propagate/add/{}/{}/{}/{}'.format(sequence_number,node_id,LC,TS),board_dict[sequence_number],'POST')) 
            t.daemon = True
            t.start()
            sequence_number = sequence_number + 1
            return True
        except Exception as e: 
            print e
        return False

    @app.post('/board/<element_id:int>/')
    def client_action_received(element_id):
        global board, node_id,entry_sequence_index,LC, TS
        try:
            # try to get user click, action_dom is action delete or modify
            action_dom = request.forms.get('delete') 
            if int(action_dom) == 0:
                modified_element = request.forms.get('entry') 
                message_string = board[element_id]
                mod_entry, mod_pre_id, mod_lc, mod_ts = message_string.split(',')
                modify_element_in_store(element_id, modified_element, mod_pre_id, mod_lc, mod_ts, False)
                propagate_to_vessels('/propagate/modify/{}/{}/{}/{}'.format(element_id,mod_pre_id,mod_lc,mod_ts),modified_element,'POST')
            elif int(action_dom) == 1:
                message_string = board[element_id]
                del_entry, del_pre_id, del_lc, del_ts = message_string.split(',')
                delete_element_from_store(element_id, del_pre_id, del_lc, del_ts, False)
                propagate_to_vessels('/propagate/delete/{}/{}/{}/{}'.format(element_id, del_pre_id,del_lc,del_ts))
            return True
        except Exception as e:
            print e
        return False

    @app.post('/propagate/<action>/<element_id:int>/<precede_vessel_ID:int>/<Logical_Clock:int>/<TimeStamp:int>')
    def propagation_received(action, element_id,precede_vessel_ID,Logical_Clock, TimeStamp):
        # check the action is add, modify or delete
        global board, sequence_number, LC, TS
        try:
            if action == 'add':
                body = request.body.read()
                if LC < Logical_Clock:
                    LC = Logical_Clock + 1
                else:
                    LC = LC + 1
                TS = Logical_Clock
                #print "\nLC:{},TS:{}\n".format(LC,TS)
                add_new_element_to_store(sequence_number, body, precede_vessel_ID, LC, TS) 
                sequence_number = sequence_number + 1
            elif action =='modify':
                body = request.body.read()
                modify_element_in_store(element_id, body, precede_vessel_ID, Logical_Clock, TimeStamp, True)
            elif action == 'delete':
                delete_element_from_store(element_id, precede_vessel_ID, Logical_Clock, TimeStamp, True)
            return True
        except Exception as e:
            print e
        return False

        
    # ------------------------------------------------------------------------------------------------------
    # EXECUTION
    # ------------------------------------------------------------------------------------------------------
    # Execute the code
    def main():
        global vessel_list, node_id, app, sequence_number,LC,TS
        LC = 0
        TS = 0
        sequence_number = 0
        port = 80
        parser = argparse.ArgumentParser(description='Your own implementation of the distributed blackboard')
        parser.add_argument('--id', nargs='?', dest='nid', default=1, type=int, help='This server ID')
        parser.add_argument('--vessels', nargs='?', dest='nbv', default=1, type=int, help='The total number of vessels present in the system')
        args = parser.parse_args()
        node_id = args.nid
        vessel_list = dict()
        # We need to write the other vessels IP, based on the knowledge of their number
        for i in range(1, int(args.nbv)+1):
            vessel_list[str(i)] = '10.1.0.{}'.format(str(i))

        try:
            run(app, host=vessel_list[str(node_id)], port=port)
        except Exception as e:
            print e
    # ------------------------------------------------------------------------------------------------------
    if __name__ == '__main__':
        main()
except Exception as e:
        traceback.print_exc()
        while True:
            time.sleep(60.)