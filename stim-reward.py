#!/bin/python3
#######################################################################################
# MOUSE NEURAL ELECTROSTIMULATION PROGRAM USING BPOD STATE MACHINE AND INTAN CONTROLLER
# (c) 2022 Purdue University
#
# Reused Example Code
# (c) 2022 Intan Technologies
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

import os, random, sys, time, socket
from pybpodapi.protocol import Bpod, StateMachine
import RPi.GPIO as GPIO
import matplotlib.pyplot as plt

# Buzzer params
BUZZER_PIN = 17         # Trigger (+) pin for buzzer
BUZZER_TIME = 1         # Time (sec) for buzzer to sound
BUZZER_DUTYCYCLE = 50   # Duty cycle (%) for buzzer

# Frequency params
INIT_FREQ = 440         # Initiation frequency (Hz)
REWARD_FREQ = 650       # Reward frequency (Hz)
PUNISH_FREQ = 800       # Punishment frequency (Hz)

# Timing params
TIMEOUT_TIME = 10       # Duration of timeout (sec)

# RHX TCP communication params
COMMAND_BUFFER_SIZE = 1024      # Size of command data buffer
WAVEFORM_BUFFER_SIZE = 200000   # Size of waveform data buffer
TCP_ADDRESS = '127.0.0.1'       # IP Address (using localhost currently)
COMMAND_PORT = 5000             # Port for sending command data
WAVEFORM_PORT = 5001            # Port for receiving waveform data

# RHX stimulation params
STIM_CHANNEL = 'a-010'  # Stimulation channel (port-channel #)
STIM_CURRENT = '10'     # Current of first phase stimulation amplitude (microamps)

# Parse softcodes from State Machine USB serial interface
def softCode(data):
    print("received " + str(data))
    if data == 1:
        # play init sound
        buzzer = GPIO.PWM(BUZZER_PIN, INIT_FREQ)

        # Send command to set board running
        scommand.sendall(b'set runmode run')

        # Stimulate
        scommand.sendall(b'execute manualstimtriggerpulse f1')

    elif data == 2:
        # play reward sound
        buzzer = GPIO.PWM(BUZZER_PIN, REWARD_FREQ)

    elif data == 3:
        # play failure sound
        buzzer = GPIO.PWM(BUZZER_PIN, PUNISH_FREQ)

    buzzer.start(BUZZER_DUTYCYCLE)
    time.sleep(BUZZER_TIME)
    buzzer.stop()

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

    # Query sample rate from RHX software
    scommand.sendall(b'get sampleratehertz')
    commandReturn = str(scommand.recv(COMMAND_BUFFER_SIZE), "utf-8")
    expectedReturnString = "Return: SampleRateHertz "
    if commandReturn.find(expectedReturnString) == -1: # Look for "Return: SampleRateHertz N" where N is the sample rate
        raise Exception('Unable to get sample rate from server')
    else:
        sampleRate = float(commandReturn[len(expectedReturnString):])

    # Calculate timestep from sample rate
    timestep = 1 / sampleRate

    # Clear TCP data output to ensure no TCP channels are enabled
    scommand.sendall(b'execute clearalldataoutputs')
    time.sleep(0.1)

    # Send TCP commands to set up TCP Data Output Enabled for wide
    # band of channel A-010
    scommand.sendall(b'set a-010.tcpdataoutputenabled true')
    time.sleep(0.1)

# Configure stimulation parameters--Credit Intan RHX Example TCP Client
def initStim():
    # Send commands to configure some stimulation parameters, and execute UploadStimParameters for that channel
    scommand.sendall(b'set ' + STIM_CHANNEL + '.stimenabled true')
    time.sleep(0.1)
    scommand.sendall(b'set ' + STIM_CHANNEL + '.source keypressf1')
    time.sleep(0.1)
    scommand.sendall(b'set ' + STIM_CHANNEL + '.firstphaseamplitudemicroamps ' + STIM_CURRENT)
    time.sleep(0.1)
    scommand.sendall(b'set a' + STIM_CHANNEL + '.firstphasedurationmicroseconds ' + BUZZER_TIME)
    time.sleep(0.1)
    scommand.sendall(b'execute uploadstimparameters ' + STIM_CHANNEL)
    time.sleep(1)

# Read waveform--Credit Intan RHX Example TCP Client
def parseWaveform():
    # Calculations for accurate parsing
    # At 30 kHz with 1 channel, 1 second of wideband waveform data (including magic number, timestamps, and amplifier data) is 181,420 bytes
    # N = (framesPerBlock * waveformBytesPerFrame + SizeOfMagicNumber) * NumBlocks where:
    # framesPerBlock = 128 ; standard data block size used by Intan
    # waveformBytesPerFrame = SizeOfTimestamp + SizeOfSample ; timestamp is a 4-byte (32-bit) int, and amplifier sample is a 2-byte (16-bit) unsigned int
    # SizeOfMagicNumber = 4; Magic number is a 4-byte (32-bit) unsigned int
    # NumBlocks = NumFrames / framesPerBlock ; At 30 kHz, 1 second of data has 30000 frames. NumBlocks must be an integer value, so round up to 235

    framesPerBlock = 128
    waveformBytesPerFrame = 4 + 2
    waveformBytesPerBlock = framesPerBlock * waveformBytesPerFrame + 4

    # Read waveform data
    rawData = swaveform.recv(WAVEFORM_BUFFER_SIZE)
    if len(rawData) % waveformBytesPerBlock != 0:
        raise Exception('An unexpected amount of data arrived that is not an integer multiple of the expected data size per block')
    numBlocks = int(len(rawData) / waveformBytesPerBlock)

    rawIndex = 0 # Index used to read the raw data that came in through the TCP socket
    amplifierTimestamps = [] # List used to contain scaled timestamp values in seconds
    amplifierData = [] # List used to contain scaled amplifier data in microVolts

    for block in range(numBlocks):
        # Expect 4 bytes to be TCP Magic Number as uint32.
        # If not what's expected, raise an exception.
        magicNumber, rawIndex = readUint32(rawData, rawIndex)
        if magicNumber != 0x2ef07a08:
            raise Exception('Error... magic number incorrect')

        # Each block should contain 128 frames of data - process each
        # of these one-by-one
        for frame in range(framesPerBlock):
            # Expect 4 bytes to be timestamp as int32.
            rawTimestamp, rawIndex = readInt32(rawData, rawIndex)
            
            # Multiply by 'timestep' to convert timestamp to seconds
            amplifierTimestamps.append(rawTimestamp * timestep)

            # Expect 2 bytes of wideband data.
            rawSample, rawIndex = readUint16(rawData, rawIndex)
            
            # Scale this sample to convert to microVolts
            amplifierData.append(0.195 * (rawSample - 32768))

# Main function
def main():
    # Init gpio
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUZZER_PIN,GPIO.OUT)

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
            output_actions=[(Bpod.OutputChannels.PWM2, 255)])   # Change Bpod LED to green to show ready

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
            output_actions=[])

        # Reward on proper action
        sma.add_state(
            state_name='Reward',
            state_timer=0.1,
            state_change_conditions={Bpod.Events.Tup: 'exit'},
            output_actions=[(Bpod.OutputChannels.Valve, rewardValve), (Bpod.OutputChannels.SoftCode, 2)])  # Reward correct choice

        # Punish
        sma.add_state(
            state_name='Punish',
            state_timer=3,
            state_change_conditions={Bpod.Events.Tup: 'exit'},
            output_actions=[(Bpod.OutputChannels.SoftCode, 3)])  # Signal incorrect choice

        my_bpod.send_state_machine(sma)  # Send state machine description to Bpod device

        print("Waiting for poke. Reward: ", 'left' if thisTrialType == 1 else 'right')

        my_bpod.run_state_machine(sma)  # Run state machine

        print("Current trial info: ", my_bpod.session.current_trial)

    my_bpod.close()  # Disconnect Bpod and perform post-run actions
    
    scommand.close() # Close TCP socket

# ENTRY

if __name__ == '__main__':
    nTrials = int(sys.argv[1])

    # Init bpod
    my_bpod = Bpod()
    my_bpod.softcode_handler_function = softCode

    # Connect to TCP command server
    print('Connecting to TCP command server...')
    scommand = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    scommand.connect((TCP_ADDRESS, COMMAND_PORT))

    # Connect to TCP waveform server
    print('Connecting to TCP waveform server...')
    swaveform = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    swaveform.connect((TCP_ADDRESS, WAVEFORM_PORT))

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