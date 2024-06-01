#!/usr/bin/python3

from scapy.all import *

class FlowTracking:
    def __init__(self, startSeqNum, ackNumReceived, srcIP, dstIP):
        self.startSeqNum = startSeqNum
        self.ackNumReceived = ackNumReceived
        self.highestSeqNum = startSeqNum
        self.pktLenOfHighestSeqNumPacket = 0
        self.srcIP = srcIP
        self.dstIP = dstIP

def readHandShake(pcap):
    # read syn
    p = pcap.pop(0)
    seqInit = p[TCP].seq
    srcInit = p[IP].src
    dstInit = p[IP].dst

    # read synack
    p = pcap.pop(0)
    if p[TCP].ack != seqInit + 1:
        print(f"ERROR: seq={seqInit}, ack={p[TCP].ack}")
    if p[IP].src != dstInit or p[IP].dst != srcInit:
        print(f"ERROR: srcInit={srcInit}, destInit={dstInit} Resp: src={p[IP].src},dst={p[IP].dst}")

    seqOther = p[TCP].seq

    # read ack
    p = pcap.pop(0)
    if p[TCP].ack != seqOther + 1:
        print(f"ERROR: seq={seqOther}, ack={p[TCP].ack}")
    if p[IP].src != srcInit or p[IP].dst != dstInit:
        print(f"ERROR: srcInit={srcInit}, destInit={dstInit} Resp: src={p[IP].src},dst={p[IP].dst}")

    return FlowTracking(seqOther, seqOther + 1, dstInit, srcInit)

def isFlowEgress(p, f):
    return p[IP].src == f.srcIP and p[IP].dst == f.dstIP

def findMaxBytesInFlight(pcapfile):
    packets = rdpcap(pcapfile)
    flow = readHandShake(packets)

    maxBytesInFlight = 0
    inFlight = 0

    for packet in packets:
        if TCP in packet:
            if isFlowEgress(packet, flow):
                seq = packet[TCP].seq
                payload_len = len(packet[TCP].payload)
                if seq >= flow.highestSeqNum:
                    flow.highestSeqNum = seq
                    flow.pktLenOfHighestSeqNumPacket = payload_len

                inFlight += payload_len

            elif packet[IP].src == flow.dstIP and packet[IP].dst == flow.srcIP:
                ack = packet[TCP].ack
                if ack > flow.ackNumReceived:
                    inFlight -= (ack - flow.ackNumReceived)
                    flow.ackNumReceived = ack

            maxBytesInFlight = max(maxBytesInFlight, inFlight)

    return maxBytesInFlight

if __name__ == '__main__':
    maxBytesInFlight = findMaxBytesInFlight("simple-tcp-session.pcap")
    print("Max: " + str(maxBytesInFlight))
    print()

    maxBytesInFlight = findMaxBytesInFlight("out_10m_0p.pcap")
    print("Max: " + str(maxBytesInFlight))
    print()
