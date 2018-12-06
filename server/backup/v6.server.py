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

from bottle import Bottle, run, request, template
import requests
import operator
# ------------------------------------------------------------------------------------------------------
try:
    app = Bottle()

    board = {0:"nothing,lc,ts,node_id"} 
    new_board = board
    # ------------------------------------------------------------------------------------------------------
    # BOARD FUNCTIONS
    # ------------------------------------------------------------------------------------------------------
    def add_new_element_to_store(entry_sequence, element, logical_clock,time_stamp):
        global board, node_id
        success = False
        try:
            board[entry_sequence] = "{},{},{},{}".format(element,logical_clock,time_stamp,node_id)
            success = True
        except Exception as e:
            print e
        return success

    def modify_element_in_store(entry_sequence, modified_element, LC):
        global board, node_id
        success = False
        try:
            board[entry_sequence] = modified_element
            success = True
        except Exception as e:
            print e
        return success

    def delete_element_from_store(entry_sequence, LC):
        global board, node_id
        success = False
        try:
            board.pop(entry_sequence)  
            success = True
        except Exception as e:
            print e
        return success

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


    # ------------------------------------------------------------------------------------------------------
    # ROUTES
    # ------------------------------------------------------------------------------------------------------
    # a single example (index) should be done for get, and one for post
    # ------------------------------------------------------------------------------------------------------
    @app.route('/')
    def index():
        global board, node_id,new_board
        for key, value in board.items():
            entry,lc,ts,nod_id = value.split(',')
            new_board[key] = entry
        return template('server/index.tpl', board_title='Vessel {}'.format(node_id), board_dict=sorted(new_board.iteritems()), \
                                            members_name_string='lhan@student.chalmers.se;shahn@student.chalmers.se')

    @app.get('/board')
    def get_board():
        global board, node_id,new_board
        for key, value in board.items():
            entry,lc,ts,nod_id = value.split(',')
            new_board[key] = entry
        print entry  #no input, print nothing
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
            print "\nLC:{},TS:{}\n".format(LC,TS)
            add_new_element_to_store(sequence_number, new_entry,LC, TS) 
            board_dict = {sequence_number : new_entry}
            t = Thread(target=propagate_to_vessels, args = ('/propagate/add/{}/{}/{}'.format(sequence_number,LC,TS),board_dict[sequence_number],'POST')) 
            t.daemon = True
            t.start()
            sequence_number = sequence_number + 1
            return True
        except Exception as e:
            print e
        return False

    @app.post('/board/<element_id:int>/')
    def client_action_received(element_id):
        global board, node_id,sequence_number, LC, TS
        try:
            # try to get user click, action_dom is action delete or modify
            action_dom = request.forms.get('delete') 
            
            return True
        except Exception as e:
            print e
        return False

    @app.post('/propagate/<action>/<element_id:int>/<Logical_Clock:int>/<TimeStamp:int>')
    def propagation_received(action, element_id,Logical_Clock, TimeStamp):
        # check the action is add, modify or delete
        global board, node_id, sequence_number, LC, TS
        try:
            if action == 'add':
                body = request.body.read()
                if LC < Logical_Clock:
                    LC = Logical_Clock + 1
                else:
                    LC = LC + 1
                TS = Logical_Clock
                print "\nafter,LC:{},TS:{}\n".format(LC,TS)
                add_new_element_to_store(sequence_number, body,LC) # you might want to change None here
                sequence_number = sequence_number + 1

            template('server/boardcontents_template.tpl',board_title='Vessel {}'.format(node_id), board_dict=sorted(board.iteritems()))
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
        for i in range(1, args.nbv):
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