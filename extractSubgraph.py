#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 10 14:20:09 2017

@author: fubao
"""


import csv
import os
from collections import OrderedDict
from random import sample

from CommonFiles.commons import mycsv_reader
from CommonFiles.commons import writeListRowToFileWriterTsv
from CommonFiles.commons import  appendStringRowToFileWriterTsv

from graphCommon import readCiscoDataGraph
from graphCommon import readdblpDataGraph


import networkx as nx
#extractSubGraph from data graph

from math import floor
import time

'''
0	product
1	vulnerability
2	bug_Id
3	workaround
4	technology
5	workgroup
6	product site
'''

class ClsSubgraphExtraction(object):

    def __init__(self):
      pass
    
    #extract query graph for experiments.
    #query graph size definition: specific node number-spn,  unknown query nodes- qn;      (spn, qn)
    #startNodeSet indicates the set with the node type of query node starting; endNodeSet indicates the node type of query node ending
    def funcExtractSubGraph(self, G, startNodeSet, endNodeSet, specNodeNum, queryNodeNum, dstTypeLst):
        
        #find path of , 
        #get the specNodeNum
        divider = floor(specNodeNum/queryNodeNum)
        residual = specNodeNum % queryNodeNum
        
        divideSpecNodeNum = []
        for i in range(queryNodeNum):              #assign specNodeNum size for each queryNodeNum
            if residual != 0:
                divideSpecNodeNum.append(divider + 1)           
                residual -= 1
            else:
                divideSpecNodeNum.append(divider)
        
        #print ("divideSpecNodeNum, : ", divideSpecNodeNum)
        
        queryGraphLst = []            # every element is a list [(nodeId, nodeId type)...]
        dstTypeIndex = 0              #which query node type
        for src in startNodeSet:
            #breakFlag = False
            for dst in endNodeSet:
                print(" xxxx ", src, dst)
                if src != dst:
                    #get all path
                    #print(" xxxx dddddd", src, dst)
                    #print ("nx.all_simple_paths: ")
                    #print (" ", list(nx.all_simple_paths(G, src, dst, cutoff= 100)))
                    #timeBegin = time.time()
                    
                    for path in nx.all_simple_paths(G, src, dst, cutoff= 11):
                        #check how many product inside the path
                        #check how many has product type in the path
                        #print(" path aaaaa", len(path))
                        prodNodes = []
                        tmpTargetIndex = 0
                        for nodeId in path:
                            if G.node[nodeId]['labelType'] == dstTypeLst[tmpTargetIndex]:
                                #print ("xxxxxxx: ", node)
                                prodNodes.append(nodeId)
                                tmpTargetIndex += 1
                                if len(prodNodes) >= queryNodeNum:
                                    break
                        if len(prodNodes) >= queryNodeNum:
                           # breakFlag = True
                            #get the 
                            #print(" resNodesPath ", path)
                            #cntQueryNum = 0
                            prevj = 0
                            for nd in path:
                                innerLst = []
                                #print(" len dstTypeLst ", len(dstTypeLst), dstTypeIndex, specNodeNum, queryNodeNum)
                                dstType = dstTypeLst[dstTypeIndex]               #get query node type
                                if G.node[nd]['labelType'] == dstType:
                                    #get node neighbor for specific number
                                    nbs = G[nd]  
                                    tmpCnt = 0
                                    j = prevj
                                    nbsLst= list(nbs.keys())
                                    #print ("type: ", type(nbs), len(nbsLst))
                                    while (j < len(nbsLst)):
                                        nb = nbsLst[j]
                                        if G.node[nb]['labelType'] != dstType and (nb, G.node[nb]['labelType']) not in innerLst:
                                            innerLst.append((nb, G.node[nb]['labelType']))
                                            tmpCnt += 1
                                            if innerLst in queryGraphLst:
                                                innerLst.pop()
                                            elif innerLst not in queryGraphLst and tmpCnt >= divideSpecNodeNum[dstTypeIndex]:  #safisfy specific number
                                                #cntQueryNum += 1
                                                queryGraphLst.append(innerLst)
                                                #print(" dstTypeIndex aa ", dstTypeIndex)
                                                dstTypeIndex += 1    #change next dstType index 
                                                if dstTypeIndex >= queryNodeNum:
                                                    #print(" queryGraphLst ", queryGraphLst)
                                                    return path, queryGraphLst
                                                break
                                        j += 1
                                    prevj = j
                                            
    
                                    
    
    #extract product data query graph   entry    
    def funcExecuteExtractQueryProduct(self, ciscoNodeInfoFile, ciscoAdjacentListFile):
 
        G = readCiscoDataGraph(ciscoAdjacentListFile, ciscoNodeInfoFile)
        
        #nodeLst = G.nodes()
        #print ("node number: ", len(nodeLst), G.node[1]['labelType'])
        
        productNodeSet = set()
        #vulnerNodeSet = set()
        for n, d in G.nodes_iter(data=True):
            if d['labelType'] == 0:
                productNodeSet.add(n)
            #if d['labelType'] == 1:
            #    vulnerNodeSet.add(n)
    
        print ("productNodeSet: ", len(productNodeSet))
        #workgroup = ((u,v) for u,v,d in G.nodes_iter(data=True) if d['labelType']==5)
        
        
       # specNodeNum = 13
       # queryNodeNum = 10
        
        specNodesQueryNodesLst = [(2, 1),(4, 2), (4,3)]    # [(2, 1),(4, 2), (4,3), (5,4), (6,5), (7,6), (8, 8), (10,10)]
        
        outFile = "../../../hierarchicalNetworkQuery/hierarchicalQueryPython/output/extractSubgraphOutput/ciscoDataExtractQueryGraph01"
        os.remove(outFile) if os.path.exists(outFile) else None
        
        fd = open(outFile,'a')
        for tpls in specNodesQueryNodesLst:
            specNodeNum = tpls[0]
            queryNodeNum = tpls[1]
            dstTypeLst = [0]*queryNodeNum
    
            path, queryGraphLst = self.funcExtractSubGraph(G, productNodeSet, productNodeSet, specNodeNum, queryNodeNum, dstTypeLst)
    
            writeLst = []              #format: x,x;x,x;    x,x;,x,x....
            for specNumLst in queryGraphLst:
                inputStr = ""
                for tpl in specNumLst[:-1]:
                    inputStr += str(tpl[0]) + "," + str(tpl[1]) + ";"
                    
                inputStr += str(specNumLst[-1][0]) + "," + str(specNumLst[-1][1])
                writeLst.append(inputStr)  
                
            writeListRowToFileWriterTsv(fd, writeLst, '\t')
    
    
    #extract dblp data query graph entry
    def funcExecuteExtractQueryDblp(self, dblpNodeInfoFile, edgeListFile, outFile):
        
        G = readdblpDataGraph(edgeListFile, dblpNodeInfoFile)
        peopleNodeSet = set()
        for n, d in G.nodes_iter(data=True):
            if d['labelType'] == 1:
                peopleNodeSet.add(n)
        print ("peopleNodeSet: ", len(peopleNodeSet))
         
        specNodesQueryNodesLst = [(2, 1),(4, 2), (4,3)]   #        [(2, 1),(4, 2), (4,3), (5,4), (6,5), (7,6), (8, 8), (10,10)]
        os.remove(outFile) if os.path.exists(outFile) else None
    
        fd = open(outFile,'a')
        for tpls in specNodesQueryNodesLst:
            specNodeNum = tpls[0]
            queryNodeNum = tpls[1]
            dstTypeLst = [1]*queryNodeNum
    
            path, queryGraphLst = self.funcExtractSubGraph(G, peopleNodeSet, peopleNodeSet, specNodeNum, queryNodeNum, dstTypeLst)
            
            writeLst = []              #format: x,x;x,x;    x,x;,x,x....
            for specNumLst in queryGraphLst:
                inputStr = ""
                for tpl in specNumLst[:-1]:
                    inputStr += str(tpl[0]) + "," + str(tpl[1]) + ";"
                    
                inputStr += str(specNumLst[-1][0]) + "," + str(specNumLst[-1][1])
                writeLst.append(inputStr)  
                
            writeListRowToFileWriterTsv(fd, writeLst, '\t')   
            


    #get subgraph from datagraph,  get 10% of data; 10%, 20%, 50, 80%, 100% 
    #accumulate rationode, including previous node set
    def subgraphFromDatagraph(self, G, rationofNodes, prevNodeSet):
        #get random number of nodes
        numberIncreaseNodes = int(len(G)*rationofNodes) - len(prevNodeSet)
        print ("G numberNodes: ", numberIncreaseNodes)
        numberNodesLst = prevNodeSet + sample(G.nodes(), numberIncreaseNodes)
        #get subgraph
        subGraph = G.subgraph(numberNodesLst)    
        
        return subGraph, numberNodesLst


    #extract subgraph from data graph
    def executeSubgraphExtractFromDatagraph(self, inputDblpNodeInfoFile, inputEdgeListFile):
        #10%, 20%, 50%, 80%, 100
        outputDir = "output/dblpDataGraphExtractOut/"       #output directory
        

        G = readdblpDataGraph(inputEdgeListFile, inputDblpNodeInfoFile)
        
        print ("G: ", len(G))
        rationofNodesLst= [0.1, 0.2, 0.5, 0.8, 1.0]
        prevNodeSet = []
        for rationofNodes in rationofNodesLst: 
            subG, numberNodesLst = self.subgraphFromDatagraph(G, rationofNodes, prevNodeSet)
            prevNodeSet = numberNodesLst
            #write out file
            directoryPath = outputDir + "dataGraphInfo" + str(rationofNodes)
            if not os.path.exists(directoryPath):
                os.makedirs(directoryPath)
            outFileEdgeLst =  directoryPath + "/edgeListPart" + str(rationofNodes)
            outFileNodeInfo = directoryPath + "/nodeInfoPart" + str(rationofNodes)
            os.remove(outFileEdgeLst) if os.path.exists(outFileEdgeLst) else None
            os.remove(outFileNodeInfo) if os.path.exists(outFileNodeInfo) else None

            #fh=open(outFile,'wb')
            #nx.write_edgelist(G, fh)
            os.remove(outFileEdgeLst) if os.path.exists(outFileEdgeLst) else None
            
            fdEdge = open(outFileEdgeLst,'a')
            fdInfo = open(outFileNodeInfo,'a')
            
            for edge in subG.edges_iter(data='edgeHierDistance', default=1):
                #print ("edge: ", edge)
                nodeId1 = int(edge[0])
                node1LabelType = G.node[nodeId1]['labelType']       #G[nolabelType(0)
                node1LabelName = G.node[nodeId1]['labelName']  
                
                nodeInfoLst1 = [node1LabelName + "+++" + str(node1LabelType), nodeId1]
                writeListRowToFileWriterTsv(fdInfo, nodeInfoLst1, '\t')
                    
                nodeId2 = int(edge[1])
                node2LabelType = G.node[nodeId2]['labelType']       #G[nolabelType(0)
                node2LabelName = G.node[nodeId2]['labelName']  
                nodeInfoLst2 = [node2LabelName + "+++" + str(node2LabelType), nodeId2]
                writeListRowToFileWriterTsv(fdInfo, nodeInfoLst2, '\t')
                
                if edge[2] == 0:
                    edgeStr = "same"
                    writeListRowToFileWriterTsv(fdEdge, [edge[0], edge[1], edgeStr], '\t')
                elif edge[2] == 1:
                    edgeStr = "higher"
                    writeListRowToFileWriterTsv(fdEdge, [edge[0], edge[1], edgeStr], '\t')
                elif edgeStr == -1:
                    edgeStr = "lower"
                    writeListRowToFileWriterTsv(fdEdge, [edge[0], edge[1], edgeStr], '\t')                    


#main 
def main():
    #query graph subtraction
    subgraphExtractionObj = ClsSubgraphExtraction()
    ciscoNodeInfoFile = "../../../hierarchicalNetworkQuery/inputData/ciscoProductVulnerability/newCiscoGraphNodeInfo"
    #ciscoAdjacentListFile = "../../../hierarchicalNetworkQuery/inputData/ciscoProductVulnerability/newCiscoGraphAdjacencyList"
    #subgraphExtractionObj.funcExecuteExtractQueryProduct(ciscoNodeInfoFile, ciscoAdjacentListFile)             #extract query graph from data graph
    
    dblpNodeInfoFile = "../dblpParserGraph/output/finalOutput/newOutNodeNameToIdFile.tsv"
    edgeListFile = "../dblpParserGraph/output/finalOutput/newOutEdgeListFile.tsv"
    outFile = "output/extractDblpQuerySizeGraph/dblpDataExtractQueryGraph.tsv"
    #subgraphExtractionObj.funcExecuteExtractQueryDblp(dblpNodeInfoFile, edgeListFile, outFile)
    
    
    #data graph subtraction
    inputEdgeListFile = "../dblpParserGraph/output/finalOutput/newOutEdgeListFile.tsv"
    inputDblpNodeInfoFile = "../dblpParserGraph/output/finalOutput/newOutNodeNameToIdFile.tsv"
    #subgraphExtractionObj.executeSubgraphExtractFromDatagraph(inputDblpNodeInfoFile, inputEdgeListFile)
    
    
    #query graph subtraction from data subgraph
    inputDblpNodeInfo01File = "output/dblpDataGraphExtractOut/dataGraphInfo0.1/nodeInfoPart0.1"   
    inputEdgeList01File = "output/dblpDataGraphExtractOut/dataGraphInfo0.1/edgeListPart0.1"   
    outFile = "output/extractDblpQuerySizeGraph/subDatagraphExtract/dblpData01ExtractQueryGraph.tsv"
    subgraphExtractionObj.funcExecuteExtractQueryDblp(inputDblpNodeInfo01File, inputEdgeList01File, outFile)             #extract query graph from data graph
    
    
if __name__== "__main__":
  main()
  
