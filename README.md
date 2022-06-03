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
pip3 install pybpod-api matplotlib
```

`pybpod-api` may require some additional dependencies--see their [site](https://pybpod.readthedocs.io/projects/pybpod-api/en/v1.8.1/) for more information

## Running
Configure the TCP command and waveform servers in the Intan RHX software on the host PC, and ensure ports and addresses match in the parameters in `stim-reward.py`. If you get an error about encoding, just run it again. It seems to be an upstream issue and running it again seems to work fine.
