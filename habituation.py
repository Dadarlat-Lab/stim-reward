#!/usr/bin/python3
###########################################################################################
# MOUSE HABITUATION PROGRAM USING BPOD STATE MACHINE AND INTAN CONTROLLER
# Thomas Makin and Kathleen Kisker
#
# MIT License
# Copyright (c) 2022, Purdue University All rights reserved.
#
# pybpod-api Sample Code
# MIT License
# Copyright (c) 2019 Scientific Software Platform, Champalimaud Foundation
#
# Stage Key:
# 1. In box, no digital feedback required
# 2. Nose poke initiation --> reward + start tone
# 3. Nose poke initiation + start tone -> nose poke response ports + reward tone
# 4. Nose poke initiation + start tone --> nose poke in correct response port + reward tone
# |
# |-> for stage 4 use stim-reward.py
#
# Softcode Key:
# 1: Initiation
# 2: Reward
#
# Bpod State Machine Port Key:
# BP 1: Left
# BP 2: Initiate
# BP 3: Right
###########################################################################################

import datetime
import os, sys
from pybpodapi.protocol import Bpod, StateMachine
import pygame
import csv

# Parse softcodes from State Machine USB serial interface
def softCode(data):
    global timestamps
    global events

    print("received " + str(data))
    timestamps.append(datetime.datetime.now().strftime("%H:%M:%S.%f"))

    # Buzzer only played for 1-3
    if data < 4:
        if data == 1:
            events.append("Reward tone")

            # play reward sound
            sound = pygame.mixer.Sound('./audio/reward.wav')
        
        else:
            events.append("Invalid code")
            return

        playing = sound.play()
        while playing.get_busy():
            pygame.time.delay(100)

# Export event data
def parseEvents():
    # Export event data as csv
    with open('event-' + date + '.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows([timestamps, events])

    print("Event data report generated!")

# Habituation stage 3 function
def stage3():
    # Init audio mixer
    pygame.mixer.init()

    # Credit: https://bit.ly/3Q0N6Af (pybpod-api protocol docs)
    for i in range(nTrials):  # Main loop
        print('Trial: ', i+1)

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
            output_actions=[])

        # Wait for response
        sma.add_state(
            state_name='WaitForResponse',
            state_timer=1,
            state_change_conditions={Bpod.Events.Port1In: 'RewardLeft', Bpod.Events.Port3In: 'RewardRight'},
            output_actions=[(Bpod.OutputChannels.PWM1, 255), (Bpod.OutputChannels.PWM3, 255)])

        # Reward for left side
        sma.add_state(
            state_name='RewardLeft',
            state_timer=0.1,
            state_change_conditions={Bpod.Events.Tup: 'exit'},
            output_actions=[(Bpod.OutputChannels.Valve, 1), (Bpod.OutputChannels.SoftCode, 1)])  # Reward + reward tone

        # Reward for right side
        sma.add_state(
            state_name='RewardRight',
            state_timer=0.1,
            state_change_conditions={Bpod.Events.Tup: 'exit'},
            output_actions=[(Bpod.OutputChannels.Valve, 3), (Bpod.OutputChannels.SoftCode, 1)])  # Reward + reward tone

        my_bpod.send_state_machine(sma)  # Send state machine description to Bpod device

        my_bpod.run_state_machine(sma)  # Run state machine

        print("Current trial info: ", my_bpod.session.current_trial)

    my_bpod.close()                       # Disconnect Bpod and perform post-run actions

# Habituation stage 2 function
def stage2():
    # Init audio mixer
    pygame.mixer.init()

    # Credit: https://bit.ly/3Q0N6Af (pybpod-api protocol docs)
    for i in range(nTrials):  # Main loop
        print('Trial: ', i+1)

        sma = StateMachine(my_bpod)

        # Wait for initiation
        sma.add_state(
            state_name='WaitForPort2Poke',
            state_timer=1,
            state_change_conditions={Bpod.Events.Port2In: 'Reward'},
            output_actions=[(Bpod.OutputChannels.PWM2, 255)])

        # Reward on proper action
        sma.add_state(
            state_name='Reward',
            state_timer=0.1,
            state_change_conditions={Bpod.Events.Tup: 'exit'},
            output_actions=[(Bpod.OutputChannels.Valve, 2)])  # Reward + init tone

        my_bpod.send_state_machine(sma)  # Send state machine description to Bpod device

        my_bpod.run_state_machine(sma)  # Run state machine

        print("Current trial info: ", my_bpod.session.current_trial)

    my_bpod.close()                       # Disconnect Bpod and perform post-run actions

# ENTRY

if __name__ == '__main__':
    if len(sys.argv) == 3:
        stage = int(sys.argv[1])
        nTrials = int(sys.argv[2])
    else:
        print("Syntax: ./habituation.py <stage: 2 | 3> <nTrials>")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

    # Parse date
    date = datetime.datetime.now().strftime("%m%d%y-%H%M")

    timestamps = []      # Timestamps for events
    events = []          # Events

    # Init bpod
    my_bpod = Bpod()
    my_bpod.softcode_handler_function = softCode

    # Handle keyboard interrupts gracefully
    try:
        if stage == 2:
            stage2()
        elif stage == 3:
            stage3()
        else:
            print("Syntax: ./habituation.py <stage: 2 | 3> <nTrials>")
            try:
                my_bpod.close()  # Reset bpod
                sys.exit(0)
            except SystemExit:
                os._exit(0)

    except KeyboardInterrupt:
        print('Interrupted')
        try:
            my_bpod.close()     # Reset bpod
            sys.exit(0)
        except SystemExit:
            os._exit(0)
