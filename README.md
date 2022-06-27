# stim-reward
A customizable python program for training mice for and controlling neural electrostimulation via an Intan Recording Controller and Bpod Finite State Machine, to be run on a Raspberry Pi. (WIP)

## Prerequisites
- Raspberry Pi (Tested on 3B+)
- Host PC running Intan RHX software
- Intan Stimulation/Recording Controller (Tested on 128-ch stimulation/recording controller)
- Bpod Finite State Machine (Tested on v2.2 with latest firmware)
- 3x Bpod reward pump modules

## Setting Up
```
Intan Controller <--> Host PC <--> Raspberry Pi <--> Bpod State Machine with Poke Modules
                                        ^
                                        |_ we are here
```

To run this software, please install the required Python modules:

```bash
pip3 install -r reqs.txt --upgrade
```

## Running
Configure the TCP command and waveform servers in the Intan RHX software on the host PC, and ensure ports and addresses match in the parameters in [`stim-reward.py`](stim-reward.py). If you get an error about encoding, just run it again. It seems to be an upstream issue and running it again seems to work fine.

[`habituation.py`](habituation.py) is meant for habituating the mice to their environment. The 4-stage process is described in the header of the file, and it is responsible for stages 2 and 3. Stage 4 (the actual experiment trials) is conducted via [`stim-reward.py`](stim-reward.py), and is the only script that includes stimulation code.

To run [`habituation.py`](habituation.py):

```
./habituation.py <stage: 2 | 3> <number of trials: (0, INF)>
```

To run [`stim-reward.py`](stim-reward.py):

```
./stim-reward.py <number of trials: (0, INF)> [<volume: (0,100]>]
```

As indicated by the [], `volume` is an optional parameter that defaults to 50 (half volume) if not indicated
