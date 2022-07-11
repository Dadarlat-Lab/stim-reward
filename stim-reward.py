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

import datetime
import os, random, sys, time, socket
from pybpodapi.protocol import Bpod, StateMachine
import pygame
import csv

# Timing params
TIMEOUT_TIME = 5    # Duration of timeout (sec)

# RHX TCP communication params
COMMAND_BUFFER_SIZE = 8192      # Size of command data buffer
TCP_ADDRESS = '128.46.90.210'       # IP Address (using localhost currently)
COMMAND_PORT = 5000             # Port for sending command data

# RHX stimulation params
STIM_CHANNEL = b'A-005'                      # Stimulation channel (port-channel #)
STIM_CURRENT = b'15'                         # Current of stimulation amplitude (microamps)
STIM_INTERPHASE = b'50'                      # Duration of interphase (microseconds)
STIM_DURATION = 200                         # Duration of stim pulse (microseconds)
STIM_TOTAL = 0.1                            # Total time of stim pulsing (sec)
STIM_FREQ = 250                             # Frequency of pulses (Hz)
STIM_TYPE = b'biphasicwithinterphasedelay'   # Type/shape of stimulation

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

            # play init sound
            sound = pygame.mixer.Sound('./audio/init.wav')

            # Stimulate
            scommand.sendall(b'execute manualstimtriggerpulse f1')

        elif data == 2:
            events.append("Success")

            # play reward sound
            sound = pygame.mixer.Sound('./audio/reward.wav')

        elif data == 3:
            events.append("Failure")

            # play punish sound
            sound = pygame.mixer.Sound('./audio/punish.wav')

        playing = sound.play()
        while playing.get_busy():
            pygame.time.delay(100)

    elif data == 10:
        events.append("NoStim")

# Read unsigned 32-bit int--Credit Intan RHX Example TCP Client
def readUint32(array, arrayIndex):
    variableBytes = array[arrayIndex : arrayIndex + 4]
    variable = int.from_bytes(variableBytes, byteorder='little', signed=False)
    arrayIndex = arrayIndex + 4
    return variable, arrayIndex

# Read signed 32-bit int--Credit Intan RHX Example TCP Client
def readInt32(array, arrayIndex):
    variableBytes = array[arrayIndex : arrayIndex + 4]
    variable = int.from_bytes(variableBytes, byteorder='little', signed=True)
    arrayIndex = arrayIndex + 4
    return variable, arrayIndex

# Read unsigned 16-bit int--Credit Intan RHX Example TCP Client
def readUint16(array, arrayIndex):
    variableBytes = array[arrayIndex : arrayIndex + 2]
    variable = int.from_bytes(variableBytes, byteorder='little', signed=False)
    arrayIndex = arrayIndex + 2
    return variable, arrayIndex

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

    # Init audio mixer
    pygame.mixer.init()

    trialTypes = [1, 2]  # 1 (rewarded left) or 2 (rewarded right)

    # Credit: https://bit.ly/3Q0N6Af (pybpod-api protocol docs)
    while 1 == 1:  # Main loop
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
            state_change_conditions={Bpod.Events.Port2In: 'RewardInit'},
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


        # Reward on init
        sma.add_state(
            state_name='RewardInit',
            state_timer=0.075,
            state_change_conditions={Bpod.Events.Tup: 'Stimulus'},
            output_actions=[(Bpod.OutputChannels.Valve, 2)])  # Reward correct choice

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


# ENTRY

if __name__ == '__main__':
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
            my_bpod.close()                       # Disconnect Bpod and perform post-run actions
            scommand.sendall(b'set runmode stop') # Stop recording
            scommand.close()                      # Close TCP socket

            # Export event data as csv
            with open('event-' + date + '.csv', 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows([timestamps, events])

            print("Event data report generated!")
            sys.exit(0)
        except SystemExit:
            os._exit(0)
