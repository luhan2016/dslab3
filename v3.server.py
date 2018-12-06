# AUTHOR:    David Bennehag    (David.Bennehag@Gmail.com)
# VERSION:    3.0
#
#    DISTRIBUTED SYSTEMS (MPCSN, Chalmers University of Technology)
#
#    Changes from V2.0:
#    * We removed the leader election and are instead going to make use of Eventual Redundancy
#    
#    * Changed from showing the local runtimes to showing the value of the logical clock in the message
#
#    TODO: 
#    * The function eventual_consistency must check the timestamps of all messages and order them correctly.
#        - Since all nodes have the same timestamps in the messages, they will reach consistency.
#
#    * Add locks in the new methods

# Used for swapping place of the two specified indexes in our messagelist
def swapMessages(indexA, indexB):
    if mycontext['reporting']:
        print "At <" + str(getruntime()) + "> ***Entered function swapMessages()***"
    
    #Perform a simple "switcheroo"
    temp = mycontext['msgList'][indexA]
    mycontext['msgList'][indexA] = mycontext['msgList'][indexB]
    mycontext['msgList'][indexB] = temp
    
    mycontext['lastSwap'] = getruntime()
    if mycontext['reporting']:
        print "At <" + str(getruntime()) + "> ***Exited function swapMessages()***\n\n"
    
# When updating the messagelist, we call this function to make sure all agree on a clock value.
# What happens is that we simply send a tiny message with our current clock value to each node.
def updateAllClocks():
    if mycontext['reporting']:
        print "At <" + str(getruntime()) + "> ***Entered function updateAllClocks()***\n\n"
    
    msgToSend = ""
    msgToSend += "<clockValue>"
    msgToSend += str(mycontext['logClock'])
    
    #mycontext['addresses'] contains a list of all our IP-addresses
    #We loop through it to connect to all vessels (ourselves excluded)
    #Then send an update to each vessel
    for address in mycontext['addresses']:            
        if address != getmyip():
            if mycontext['reporting']:
                print "sending update to: " + address
                
            newConn = openconn(address, 63165)
            newConn.send(msgToSend)
            newConn.close()

    if mycontext['reporting']:
        print "At <" + str(getruntime()) + "> ***Exited function updateAllClocks()***\n\n"
    
# Gets called by the other nodes
# as a result of receiving the "<clockValue>" message from the updateAllClocks()-function.
# Input "otherClock" is the timestamp received in the message
def compareClocks(otherClock):
    if mycontext['reporting']:
        print "At <" + str(getruntime()) + "> ***Entered function compareClocks()***\n\n"
    
    mycontext['lock'].acquire()
    
    if otherClock > mycontext["logClock"]:
        #Synchronize
        print "Someone else had a higher clock value, synchronize"
        mycontext["logClock"] = otherClock
    
    mycontext['lock'].release()
    
    if mycontext['reporting']:
        print "At <" + str(getruntime()) + "> ***Exited function compareClocks()***\n\n"
    
# Gets called after a timeout timer of a set amount of time
# Will make sure all messages are in the right order, both with respect to timestamps and IP-addresses
def eventual_consistency():
    if mycontext['reporting']:
        print "At <" + str(getruntime()) + "> ***Entered function eventual_consistency()***\n\n"
    
    # Do a check if the list is empty. If not empty, sort it and put all entries in the correct index
    if not mycontext['msgList']:
        if mycontext['reporting']:
            print "List is empty\n"
    else:
        # A loop that will go through our list of messages and check that all timestamps are in the correct, ascending, order
        counter = 0;
        for entry in mycontext['msgList']:
            print "Comparing timestamps in " + str(counter) + " and " + str(counter+1)
            # Check that both indexes exist (i.e. not at the end of list)
            if counter+1 != len(mycontext['msgList']):   
                # Get the timestamps from the two messages to compare 
                timestampA = int(mycontext['msgList'][counter][1].split("<")[1].split(">")[0])
                timestampB = int(mycontext['msgList'][counter+1][1].split("<")[1].split(">")[0])
                
                # Check to see if the two timestamps are equal
                if timestampA > timestampB:
                    # If timestampA is bigger, it means they are in the wrong order and needs to be swapped
                    print "Need to swap index " + str(counter) + " and " + str(counter+1) + ", timestamps in wrong order"
                    swapMessages(counter, counter+1)                  
                        
                else:
                    if mycontext['reporting']:
                        print "Timestamps need not be swapped"
                
                counter = counter + 1
                
            else:
                if mycontext['reporting']:
                    print "Reached end of list  <timestamps>"
        
        # A loop that will go through our list of messages and check all messages with same timestamp.
        # It will swap messages around if they are in the wrong order, according to IP
        counter = 0;
        for entry in mycontext['msgList']:
            if mycontext['reporting']:
                print "\nComparing messages " + str(counter) + " and " + str(counter+1)  
            # Check that both indexes exist (i.e. not at the end of list)
            if counter+1 != len(mycontext['msgList']):
                # Get the timestamps from the two messages to compare 
                timestampA = int(mycontext['msgList'][counter][1].split("<")[1].split(">")[0])
                timestampB = int(mycontext['msgList'][counter+1][1].split("<")[1].split(">")[0])
                
                # Check to see if the two timestamps are equal
                if timestampA == timestampB:
                    # If timestamps are equal, the highest IP-address wins
                    addressA = mycontext['msgList'][counter][1].split("> ").pop().split(":")[0].replace('.', '')
                    if mycontext['reporting']:
                        print "<" + str(timestampA) + ">" + " addressA == " + addressA
                    
                    addressB = mycontext['msgList'][counter+1][1].split("> ").pop().split(":")[0].replace('.', '')
                    if mycontext['reporting']:
                        print "<" + str(timestampB) + ">" + " addressB == " + addressB
                    
                    # If the second address is higher, it's message should come first
                    if int(addressB) > int(addressA):
                        if mycontext['reporting']:
                            print "Need to swap index " + str(counter) + " and " + str(counter+1) + ", messages in wrong order"
                        swapMessages(counter, counter+1)
                    else:
                        if mycontext['reporting']:
                            print "Messages in correct order, according to IP"
                        
                else:
                    if mycontext['reporting']:
                        print "Timestamps not identical"
                    
                counter = counter + 1
            else:
                if mycontext['reporting']:
                    print "Reached end of list  <messages>"
            
    
        #Rebuild the updated message from the sorted list and reach consistency
        newMessage = ""
        for entry in mycontext['msgList']:
            newMessage += entry[1]
        
        mycontext['message'] = newMessage
    
    if mycontext['reporting']:
        print "At <" + str(getruntime()) + "> ***Exited function eventual_consistency()***\n\n"
    
    
# Whenever we do a POST, or someone else does, this function gets called to determine that 
# messages timestamp and update our clock accordingly.
def updateLogClock(lastMessage):
    if mycontext['reporting']:
        print "At <" + str(getruntime()) + "> ***Entered function updateLogClock()***\n\n"
    
    #If the message is not empty, it means we did not do the POST.
    if(lastMessage != ""):
        if mycontext['reporting']:
            print "Someone else POSTed"
        
        timestamp = int(lastMessage.split(">")[0][1:])
        if mycontext['reporting']:
            print "Message timestamp: " + str(timestamp) 
            print "My clock value: " + str(mycontext['logClock'])        
        
        if timestamp > mycontext['logClock']:
            #If the other nodes timestamp is higher than our logical clock, synchronize the clocks and add one
            if mycontext['reporting']:
                print "Synch our clocks"
            mycontext['logClock'] = timestamp + 1
            
            
        elif timestamp == mycontext['logClock']:
            #If they are equal, just increase our clock
            if mycontext['reporting']:
                print "Just increase clock"
            mycontext['logClock'] = mycontext['logClock'] + 1
            
    #Else, we did the POST and do not need to check the timestamp, just increase it
    else:
        #Increase our logical clock by one when sending a message
        if mycontext['reporting']:
            print "We POSTed, just increase our clock"
        mycontext['logClock'] = mycontext['logClock'] + 1
      
    if mycontext['reporting']:
        print "At <" + str(getruntime()) + "> ***Exited function updateLogClock()***\n\n"   
    
# Add a new message to our messagelist
def updateMsgList(lastMessage):
    if mycontext['reporting']:
        print "At <" + str(getruntime()) + "> ***Entered function updateMsgList()***\n\n"
    
    if lastMessage == '':
        return
    
    mycontext['msgList'].append((mycontext['logClock'], lastMessage))
    if mycontext['reporting']:
        print "Appended value to msgList: " + lastMessage + "\n"  
    
    if mycontext['reporting']:
        print "At <" + str(getruntime()) + "> ***Exited function updateMsgList()***\n\n"
    
# Print the list of messages
def printMsgList():
    
    print "\n========================================="
    print "Current msgList:\n"
    
    for entry in mycontext['msgList']:
        print "Timestamp == " + str(entry[0])
        print "Message   == " + entry[1] + ""
        
    print "=========================================\n" 
    
# Will try and cancel ongoing timers before they trigger and set new ones.
# Is called each time we receive an update from one of the nodes
def setTimers():
    #mycontext['lock'].acquire()
    # Try to cancel the eventualConsistencyTimer, then start a new one
    try:
        #Cancel the previous timer and start a new one
        if(canceltimer(mycontext['eventualConsistencyTimer'])):
            print "Successfully canceled EC timer!"
        else:
            print "Couldn't cancel EC timer"
    except:
        print "Problem with EC timer"  
    # Try to cancel the updateClockTimer, then start a new one
    #try:
        #Cancel the previous timer and start a new one
        #if(canceltimer(mycontext['eventualConsistencyTimer'])):
            #print "Successfully canceled UC timer!"
        #else:
            #print "Couldn't cancel UC timer"
    #except:
        #print "Problem with UC timer"
    
    mycontext['eventualConsistencyTimer'] = settimer(5, eventual_consistency, ())
    #mycontext['updateClockTimer'] = settimer(15, updateAllClocks, ())
    #mycontext['lock'].release()    

### A function that receives the information to show and
### then builds the HTML to send back to the browser.
### INPUT: All the info to be added to the HTML, including the message itself
### OUTPUT: the HTML string to send
def buildHTML():
    if mycontext['reporting']:
        print "At <" + str(getruntime()) + "> ***Entered function buildHTML()***"
    
    newMessage = """
        <html>
        <head>
            <meta content="text/html; charset=utf-8" http-equiv="content-type">
            <title>Blackboard, the greatest</title>
            <style>
            body{background-color:teal; font-family: "Comic Sans MS", "Comic Sans", cursive;}
            
            </style>
        </head>
        <body>
            <h2> THE Blackboard (your IP: [""" + str(mycontext['vesselAddress']) + """], your ID: """ + str(mycontext['vesselID']) + """)</h2>
            <p>My current clock: """ + str(mycontext['logClock']) + """</p>
            <p>Last swap was at: """ + str(mycontext['lastSwap']) + """</p>
            <h3> Logical clocks   &   sender </h3>
              <p>""" + mycontext['message'] + """</p>
            <br>
            <textarea rows="4" cols="50" name="comment" form="usrform"></textarea>
            <form action="" id="usrform" method="post">
                <input type="submit">                
            </form>
        </body>
        </html>"""
    
    if mycontext['reporting']:
        print "At <" + str(getruntime()) + "> ***Finished function buildHTML()\n\n***"
        
    return newMessage
    
### END OF FUNCTION buildHTML ###        
        
### The primary building block of the program. 
### Is called every time a TCP connection is made to the local IP and port.
### It will look at the header and perform different actions depending on what kind of
### message we received.
def main(ip, port, sockobj, thiscommhandle, listencommhandle):
    if mycontext['reporting']:
        print "At <" + str(getruntime()) + "> ***Entered function main()***"
    
    #httpHeader will contain the string we received in the message coming in on the recently established connection
    httpHeader = ""
    
    try:
        # Receive the message
        httpHeader = sockobj.recv(4096)
    except:
        print "Problem with socket"  
    
    if mycontext['reporting']:
        print "Received HTTP-message: \n" + httpHeader
    
    # React differently depending on the message type: HTTP GET or POST, or some other type of communication.
    if httpHeader.startswith( 'GET' ):
        #Will initiate a conversation that leads to all clocks getting updated
        updateAllClocks()
        
        #Pass the message and the vesselID to a function that builds the HTML for us, defined above
        htmlResponse = buildHTML()
        
        #Send to the client, the HTML that was requested
        sockobj.send("HTTP/1.1 200 OK\r\nContent-type: text/html\r\n" + \
        "Content-length: %i\r\n\r\n%s" % (len(htmlResponse), htmlResponse))
        #The socket is closed at the end of the function!
        
    elif httpHeader.startswith( 'POST' ):
        
        #Prevent the user from just printing empty lines by checking that the message is not empty
        if httpHeader.split('comment=').pop() != "":
            
            #Add a tag to the start of each new message to easily identify it later
            mycontext['message'] += "<StartOfMsg>"
            
            #Add some control data to each message
            mycontext['message'] += "<" + str(mycontext['logClock']) + "> " + str(getmyip()) + ":\t "
            
            #Get the message contained in the header. Split the long string when we find the comment,
            # and then take the second string in the resulting list, which is our message as the comment
            # always comes last in the header
            newMsg = httpHeader.split('comment=').pop()
            newMsg = newMsg.replace("+", " ")
            newMsg = newMsg.replace("%0D", "")
            newMsg = newMsg.replace("%0A", "")
            mycontext['message'] += newMsg
            
            #Add a newline to prevent it all from ending up on one line in the html source code
            mycontext['message'] += "\n"
            
            #Add a break-tag to get each message on a new line
            mycontext['message'] += "<br />"
        
        msgToPost = mycontext['message'].split('<StartOfMsg>').pop()
        #mycontext['addresses'] contains a list of all our IP-addresses
        #We loop through it to connect to all vessels (ourselves excluded)
        #Then send an update to each vessel
        for address in mycontext['addresses']:            
            if address != getmyip():
                if mycontext['reporting']:
                    print "sending update to: " + address
                    
                newConn = openconn(address, 63165)
                newConn.send(msgToPost)
                newConn.close()
        
        updateMsgList(msgToPost)
        updateLogClock("")
        
        #Pass the message and the vesselID to a function that builds the HTML for us, defined above
        htmlResponse = buildHTML()
        
        #Send to the client, the HTML that was updated
        sockobj.send("HTTP/1.1 200 OK\r\nContent-type: text/html\r\n" + \
        "Content-length: %i\r\n\r\n%s" % (len(htmlResponse), htmlResponse))
        #The socket is closed at the end of the function!
        
    elif httpHeader.startswith('<clockValue>'):
        otherClock = int(httpHeader.replace("<clockValue>", ""))
        compareClocks(otherClock)
    
    #We received an update from one of the other vessels
    else:        
        updateMsgList(httpHeader)
        updateLogClock(httpHeader)        
        
        #Update our message
        mycontext['message'] += httpHeader
        
        #Set our timers each time we receive a message
        setTimers()
    
    #We close the socket that was passed in
    sockobj.close()
    
    if mycontext['reporting']:
        print "At <" + str(getruntime()) + "> ***Finished function main()\n\n***"
        
if callfunc == 'initialize':
    #Set to false to disable reporting of runtimes and other info
    mycontext['reporting'] = False
    
    if mycontext['reporting']:
        print "At <" + str(getruntime()) + "> ***STARTING initialization***"
    
    #Create a lock to be used for Mutual Exclusion.
    #Before altering global variables, we want to acquire() a lock.
    mycontext['lock'] = getlock()
    
    #Initialize global variables
    mycontext['message'] = ""
    mycontext['vesselAddress'] = getmyip()
    #Create a (hopefully) unique ID for each vessel, ranging between 0 and 999999.
    mycontext['vesselID'] = int(randomfloat()*1000000)
    
    #Will be our logical clock that is updated for every message
    mycontext['logClock'] = 0
    
    #The list containing messages. Contains tuples with timestamps and messages.
    mycontext['msgList'] = []
    
    #Will keep track of at what time we did our last swap, for measuring purposes
    mycontext['lastSwap'] = 0.0
    
    #Open() the file with IP-addresses, remember to close() when finished
    ipFile = open('ipaddress.txt', 'r')
    #We read() the file and split() the lines up into separate entries, returning a list of addresses
    mycontext['addresses'] = ipFile.read().split()
    ipFile.close()  
    
    if len(callargs) > 1:
        raise Exception("Too many call arguments")
    
    # Running remotely (assuming that we pass input argument only remotely):
    # whenever this vessel gets a connection on its IPaddress:Clearinghouseport it'll call function main
    elif len(callargs) == 1:
        mycontext['port'] = int(callargs[0])
        ip = mycontext['vesselAddress']    
     
    else:
        mycontext['port'] = 63165
        ip = mycontext['vesselAddress']
        
    # Running locally:
    # whenever we get a connection on 127.0.0.1:12345 we'll call main
    #else:
    #    port = 63165
    #    ip = '127.0.0.1'
    
    
    #call function main() whenever we receive a TCP connection
    waitforconn(mycontext['vesselAddress'], mycontext['port'], main)
    
    if mycontext['reporting']:
        print "At <" + str(getruntime()) + "> ***FINISHED initialization***\n\n"
    
    
    # wait 5 seconds, then call eventual_consistency()    
    #mycontext['eventualConsistencyTimer'] = settimer(5, eventual_consistency,())
    
    #Wait for all vessels to get ready, some appear to be really slow...
    #sleep(5)
    
    
    
    

        
    

