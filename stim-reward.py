#!/usr/bin/python3
#######################################################################################
# MOUSE NEURAL ELECTROSTIMULATION PROGRAM USING BPOD STATE MACHINE AND INTAN CONTROLLER
# Thomas Makin and Kathleen Kisker
#
# MIT License
# Copyright (c) 2022, Purdue University All rights reserved.
#
# pybpod-api Sample Code
# MIT License
# Copyright (c) 2019 Scientific Software Platform, Champalimaud Foundation
#
# Intan TCP Sample Code
# Public Domain
# Copyright (c) 2022, Intan Technologies
#
# Softcode Key:
# 1: Stimulation
# 2: Reward
# 3: Punishment
#
# Bpod State Machine Port Key:
# BP 1: Left
# BP 2: Initiate
# BP 3: Right
#######################################################################################

import csv, datetime, os, random, socket, subprocess, sys, time # Builtin lib imports
import pysine                                                   # Sine freq generator
from pybpodapi.protocol import Bpod, StateMachine               # Python Bpod API

# Timing params
TIMEOUT_TIME = 5    # Duration of timeout (sec)

# RHX TCP communication params
COMMAND_BUFFER_SIZE = 8192      # Size of command data buffer
TCP_ADDRESS = '128.46.90.210'   # IP Address (using localhost currently)
COMMAND_PORT = 5000             # Port for sending command data

# RHX stimulation params
STIM_CHANNEL = b'A-000'                      # Stimulation channel (port-channel #)
STIM_CURRENT = b'25'                         # Current of stimulation amplitude (microamps)
STIM_INTERPHASE = b'50'                      # Duration of interphase (microseconds)
STIM_DURATION = 200                          # Duration of stim pulse (microseconds)
STIM_TOTAL = 0.1                             # Total time of stim pulsing (sec)
STIM_FREQ = 250                              # Frequency of pulses (Hz)
STIM_TYPE = b'biphasicwithinterphasedelay'   # Type/shape of stimulation

# Audio params
STIM_TONE = 15000       # Stim tone frequency (Hz)
REWARD_TONE = 18000     # Reward tone frequency (Hz)
PUNISH_TONE = 22000     # Punishment tone frequency (Hz)
DEFAULT_VOLUME = "50%"  # Defualt volume (if optional arg not set)
RESPONSE_VOLUME = "50%" # Volume for reward and punishment tones--NOT CONTROLLED BY ARGUMENT

# Parse softcodes from State Machine USB serial interface
def softCode(data):
    global timestamps
    global events

    print("received " + str(data))
    timestamps.append(datetime.datetime.now().strftime("%H:%M:%S.%f"))

    # Buzzer only played for 1-3
    if data < 4:
        if data == 1:
            events.append("Stim")

            # Set volume via amixer subprocess
            subprocess.call(["amixer", "-D", "pulse", "sset", "Master", volume])

            # play stim sound (convert duration in ms to seconds)
            pysine.sine(frequency=STIM_TONE, duration=(STIM_DURATION * 0.001))

            # Stimulate
            scommand.sendall(b'execute manualstimtriggerpulse f1')

        elif data == 2:
            events.append("Success")

            # Set volume via amixer subprocess
            subprocess.call(["amixer", "-D", "pulse", "sset", "Master", RESPONSE_VOLUME])

            # play reward sound
            pysine.sine(frequency=REWARD_TONE, duration=(STIM_DURATION * 0.001))

        elif data == 3:
            events.append("Failure")

            # Set volume via amixer subprocess
            subprocess.call(["amixer", "-D", "pulse", "sset", "Master", RESPONSE_VOLUME])

            # play punish sound
            pysine.sine(frequency=PUNISH_TONE, duration=(STIM_DURATION * 0.001))

    elif data == 10:
        events.append("NoStim")

# TCP connection initialization--Credit Intan RHX Example TCP Client
def tcpInit():
    # Query runmode from RHX software
    scommand.sendall(b'get runmode')
    commandReturn = str(scommand.recv(COMMAND_BUFFER_SIZE), "utf-8")
    isStopped = commandReturn == "Return: RunMode Stop"

    # If controller is running, stop it
    if not isStopped:
        scommand.sendall(b'set runmode stop')
        time.sleep(0.1) # Allow time for RHX software to accept this command before the next one comes

    # Send command to RHX software to set baseFileName
    scommand.sendall(b'set filename.basefilename recording-' + date.encode('utf-8') + b'.rhs')
    time.sleep(0.1)

    # Send command to RHX software to set path
    scommand.sendall(b'set filename.path /home/dadarlatlab')
    time.sleep(0.1)

# Configure stimulation parameters--Credit Intan RHX Example TCP Client
def initStim():
    numPulse = str(int(STIM_FREQ * STIM_TOTAL))
    # Send commands to configure some stimulation parameters, and execute UploadStimParameters for that channel
    scommand.sendall(b'set usefastsettle true')
    time.sleep(0.1)
    scommand.sendall(b'set ' + STIM_CHANNEL + b'.stimenabled true')
    time.sleep(0.1)
    scommand.sendall(b'set ' + STIM_CHANNEL + b'.source keypressf1')
    time.sleep(0.1)
    scommand.sendall(b'set ' + STIM_CHANNEL + b'.shape ' + STIM_TYPE)
    time.sleep(0.1)

    if b"interphase" in STIM_TYPE:
        scommand.sendall(b'set ' + STIM_CHANNEL + b'.interphasedelaymicroseconds ' + STIM_INTERPHASE)
        time.sleep(0.1)

    scommand.sendall(b'set ' + STIM_CHANNEL + b'.pulseortrain PulseTrain')
    time.sleep(0.1)
    scommand.sendall(b'set ' + STIM_CHANNEL + b'.polarity NegativeFirst')
    time.sleep(0.1)
    scommand.sendall(b'set ' + STIM_CHANNEL + b'.numberofstimpulses ' + bytes(numPulse, 'utf-8'))
    time.sleep(0.1)
    scommand.sendall(b'set ' + STIM_CHANNEL + b'.firstphaseamplitudemicroamps ' + STIM_CURRENT)
    time.sleep(0.1)
    scommand.sendall(b'set ' + STIM_CHANNEL + b'.firstphasedurationmicroseconds ' + str(STIM_DURATION).encode('utf-8'))
    time.sleep(0.1)
    scommand.sendall(b'set ' + STIM_CHANNEL + b'.secondphaseamplitudemicroamps ' + STIM_CURRENT)
    time.sleep(0.1)
    scommand.sendall(b'set ' + STIM_CHANNEL + b'.secondphasedurationmicroseconds ' + str(STIM_DURATION).encode('utf-8'))
    time.sleep(0.1)
    scommand.sendall(b'execute uploadstimparameters ' + STIM_CHANNEL)
    time.sleep(1)

    # Send command to RHX software to begin recording
    scommand.sendall(b'set runmode record')

# Main function
def main():
    # Init TCP connection
    tcpInit()
    initStim()

    trialTypes = [1, 2]  # 1 (rewarded left) or 2 (rewarded right)

    # Credit: https://bit.ly/3Q0N6Af (pybpod-api protocol docs)
    for i in range(nTrials):  # Main loop
        print('Trial: ', i+1)
        thisTrialType = random.choice(trialTypes)  # Randomize trial type

        stim = False

        # Stim trial
        if thisTrialType == 1:
            stim = True
            leftAction = 'Reward'
            rightAction = 'Punish'
            rewardValve = 1

        # Non stim trial
        elif thisTrialType == 2:
            leftAction = 'Punish'
            rightAction = 'Reward'
            rewardValve = 3

        sma = StateMachine(my_bpod)

        # Wait for initiation
        sma.add_state(
            state_name='WaitForPort2Poke',
            state_timer=1,
            state_change_conditions={Bpod.Events.Port2In: 'Stimulus'},
            output_actions=[(Bpod.OutputChannels.PWM2, 255)])

        # Perform stimulus
        sma.add_state(
            state_name='Stimulus',
            state_timer=0.1,
            state_change_conditions={Bpod.Events.Tup: 'WaitForResponse'},
            output_actions=[(Bpod.OutputChannels.SoftCode, 1 if stim else 10)])

        # Wait for response
        sma.add_state(
            state_name='WaitForResponse',
            state_timer=1,
            state_change_conditions={Bpod.Events.Port1In: leftAction, Bpod.Events.Port3In: rightAction},
            output_actions=[(Bpod.OutputChannels.PWM1, 255), (Bpod.OutputChannels.PWM3, 255)])

        # Reward on proper action
        sma.add_state(
            state_name='Reward',
            state_timer=0.15,
            state_change_conditions={Bpod.Events.Tup: 'exit'},
            output_actions=[(Bpod.OutputChannels.Valve, rewardValve), (Bpod.OutputChannels.SoftCode, 2)])  # Reward correct choice

        # Punish
        sma.add_state(
            state_name='Punish',
            state_timer=TIMEOUT_TIME,
            state_change_conditions={Bpod.Events.Tup: 'exit'},
            output_actions=[(Bpod.OutputChannels.SoftCode, 3)])  # Signal incorrect choice

        my_bpod.send_state_machine(sma)  # Send state machine description to Bpod device

        print("Waiting for poke. Reward: ", 'left' if thisTrialType == 1 else 'right')

        my_bpod.run_state_machine(sma)  # Run state machine

        print("Current trial info: ", my_bpod.session.current_trial)

    my_bpod.close()                       # Disconnect Bpod and perform post-run actions

    scommand.sendall(b'set runmode stop') # Stop recording

    scommand.close()                      # Close TCP socket

    # Export event data as csv
    with open('event-' + date + '.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows([timestamps, events])

    print("Event data report generated!")

# ENTRY

if __name__ == '__main__':
    # Exit if improper syntax
    argLen = len(sys.argv)
    if argLen < 2 | argLen > 3:
        print("Syntax: ./stim-reward.py <nTrials> [<volume>]")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    
    # Parse args
    nTrials = int(sys.argv[1])
    if argLen == 3:
        volume = str(sys.argv[2]) + "%"
    else:
        volume = DEFAULT_VOLUME          # Use default volume if no volume specififed

    # Parse date
    date = datetime.datetime.now().strftime("%m%d%y-%H%M")

    timestamps = []      # Timestamps for trial events
    events = []          # Trial events

    # Init bpod
    my_bpod = Bpod()
    my_bpod.softcode_handler_function = softCode

    # Connect to TCP command server
    print('Connecting to TCP command server...')
    scommand = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    scommand.connect((TCP_ADDRESS, COMMAND_PORT))

    # Handle keyboard interrupts gracefully
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            my_bpod.close()     # Reset bpod
            scommand.close()    # Close TCP socket
            sys.exit(0)
        except SystemExit:
            os._exit(0)
