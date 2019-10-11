#!/Library/Frameworks/Python.framework/Versions/3.7/bin/python3.7
'''
Parse through the terraform directory and check each folder
to make sure no config is up and running.

Abhishikt
'''

import os
import shlex
import subprocess as sp
import sys
import threading
import time

BASEDIR="/Users/abhishikt/terraform/"
TFFILES=[]
PROVIDERS=[]
PROJECTFILES={}
PROJECTS={}

def loadData():
    global BASEDIR, TFFILES, PROVIDERS, PROJECTS, PROJECTFILES
    x=0
    for root, files, dirs in os.walk(BASEDIR):
        if x == 0:
            PROVIDERS=files
            for file in PROVIDERS:
                PROJECTS[file]=list()
        for file in dirs:
            if file.split('.')[-1] == 'tf':
                if os.path.split(os.path.split(root)[0])[-1] in PROVIDERS:
                    provider=os.path.split(os.path.split(root)[0])[-1]
                    project=os.path.split(root)[-1]
                    if project not in PROJECTFILES.keys():
                        PROJECTFILES[project] = list()
                    if project not in PROJECTS[provider]:
                        PROJECTS[provider].append(project)
                    PROJECTFILES[project].append(os.path.join(root, file))
                    # print("Provider: '{}' Project '{}' | **".format(provider, project), end='')
                    # print("{}".format(os.path.join(root, file)))
                TFFILES.append(os.path.join(root, file))
        x=x+1

def askToStop(running):
    project = os.path.split(os.path.dirname(running))[-1]
    provider = os.path.split(os.path.split(os.path.dirname(running))[0])[-1]
    print("Project: {:>10}".format(project))
    print("Provider: {:>10}".format(provider))
    answer=input("Do you want to stop above project? [Yes/No]: ")
    if answer.lower() == "yes":
        print("Stopping project...")
        if stopRunning(running) == 0:
            return(0)
        else:
            return(1)
    else:
        return(1)

def runProcess(exeString):
    initCmd = shlex.split(exeString)
    try:
        sp.check_output(initCmd)
        return(0)
    except:
        print("ERROR: Could not initialise Terraform environment")
        return(1)

def stopRunning(running):
    project = os.path.split(os.path.dirname(running))[-1]
    provider = os.path.split(os.path.split(os.path.dirname(running))[0])[-1]
    print("Project: {:>10}".format(project))
    print("Provider: {:>10}".format(provider))
    # -state= file -> full path of .tfstate file ("running" variable)
    # -auto-approve -> to avoid asking Yes question
    terraformInitCmd = "terraform init {}".format(os.path.dirname(running))
    stateChkCMDString = "terraform destroy -auto-approve -state={}".format(running)
    ## Was trying to put the terraform commands in a thread so can show the progress as .....
    ## but for some reason the while loop (t.is_alive()) isn't working.
    #initCmd=shlex.split(terraformInitCmd)
    # t = threading.Thread(target=runProcess, name="ChildT1",
    #                      args=(str(terraformInitCmd)))
    # t.start()
    # print("Is Thread Running -> {}".format(t.is_alive()))
    # while t.is_alive():
    #     print(".",end='')
    #     time.sleep(2)

    initCmd=shlex.split(terraformInitCmd)
    try:
        sp.check_output(initCmd)
    except:
        print("ERROR: Could not initialise Terraform environment")
        return(1)

    cmdF=shlex.split(stateChkCMDString)
    try:
        sp.check_output(cmdF)
    except:
        print("ERROR: could not execute terraform destroy...")
        return(1)

    print("........STOPPED")
    return(0)

if __name__ == '__main__':
    #Running from program executing the code
    # ---- GLOBALS ----
    # PROVIDERS = []
    # PROJECTFILES = {}
    # PROJECTS = {}
    print("Searching {}".format(BASEDIR))
    loadData()
    ## WORKING PRINT of Providers / Projects / Files, Sample Output pasted below,
    '''
    Docker    
            web01             
                            /Users/abhishikt/terraform/Docker/web01/webserver.tf
    AWS       
         kubecluster          
                        /Users/abhishikt/terraform/AWS/kubecluster/kubemaster.tf
            vpc01             
                                /Users/abhishikt/terraform/AWS/vpc01/provider.tf
    '''
    # for providers in PROVIDERS:
    #     print("{:10}".format(providers))
    #     for projects in PROJECTS[providers]:
    #         print("{:^30}".format(projects))
    #         for files in PROJECTFILES[projects]:
    #             print("{:>80}".format(files))
    stateChkCMDString="terraform state list"
    stateFile="terraform.tfstate"
    toCheck=[]
    for provider in PROVIDERS:
        print("\n<<Provider: {}>>".format(provider))
        for project in PROJECTS[provider]:
            stateFileFull=os.path.join(BASEDIR,provider,project,stateFile)
            if not os.path.exists(stateFileFull):
                print("Project: {:>15}{:.>20}".format(project, "NEVER RAN"))
                continue
            print("Project: {:>15}".format(project), end='')
            isUp=False
            cmdP=shlex.split(stateChkCMDString+" -state={}".format(stateFileFull))
            for output in sp.check_output(cmdP).decode('utf-8'):
                line = []
                if output != '\n':
                    line.append(output)
                else:
                    isUp=True
            if isUp:
                print("{:.>20}".format("** RUNNING **"))
                toCheck.append(stateFileFull)
            else:
                print("{:.>20}".format("DOWN"))

    while len(toCheck) > 0:
        ans=input("\nWould you like to stop Running Project? [Yes/No/All] : ")
        if ans.lower() == "all":
            for running in toCheck:
                if stopRunning(running) == 0:
                    toCheck.pop(toCheck.index(running))
                else:
                    print("ERROR while stopping: {}".format(running))
                    sys.exit(1)
        elif ans.lower() == "yes":
            for running in toCheck:
                if askToStop(running) == 0:
                    toCheck.pop(toCheck.index(running))
                else:
                    print("ERROR while stopping: {}".format(running))
                    # sys.exit(1)
        elif ans.lower() == "no":
            print("Exiting....")
            sys.exit(0)
        else:
            print("Incorrect choice..stopping...TRY AGAIN...")