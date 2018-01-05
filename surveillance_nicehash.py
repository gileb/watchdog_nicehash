import os
import re
import time
import psutil
import logging
import glob
import progressbar
import datetime
import win32file
import msvcrt
import pywintypes
import sys

processus_a_recuperer = "excavator.exe"
# processus_a_recuperer = "sleep"
line_regex = re.compile(r".*CUDA error 'an illegal instruction.*$")
output_filename = os.path.normpath("./surveillance_nicehash.log")
# pour windows
nhm2_exec_path = os.path.expanduser('~') + "\\AppData\\Roaming\\nhm2\\bin\\excavator_server\\"

# pour test sur mac
# nhm2_exec_path=os.path.expanduser('~')+"/developpement/nicehash/"
#print(nhm2_exec_path)

# on recupere le dernier fichier ouvert dans le repertoire


def derniere_log(nhm2_exec_path):
    "objectif : trouver le dernier fichier log ouvert"

    liste_de_fichiers = glob.glob(nhm2_exec_path + "log*")
    #print(liste_de_fichiers)

    # la log a rÃ©cuperer est le dernier fichier log* modifiÃ©
    log_a_surveiller = max(liste_de_fichiers, key=os.path.getctime)
    print(datetime.datetime.now(),"=> fichier Log : ",log_a_surveiller)
    return(log_a_surveiller)


def restart_program():
    """comme son nom lindique...."""
    print(datetime.datetime.now(),"=> Relance du programme")
    python = sys.executable
    os.execl(python, python, * sys.argv)



def tail(theFile):
    "equivalent de tail -f en unix"
    compteur2=0
    flag_relance=0

    # had to do a while true because file disapears sometimes while trying to open it
    #i guess file disapears between call derniere_log and now
    while True:
        try:
            handle = win32file.CreateFile(theFile,
                                          win32file.GENERIC_READ,
                                          win32file.FILE_SHARE_DELETE |
                                          win32file.FILE_SHARE_READ |
                                          win32file.FILE_SHARE_WRITE,
                                          None,
                                          win32file.OPEN_EXISTING,
                                          0,
                                          None)

        except pywintypes.error as e:
            print("Erreur : ",e)
            log_a_surveiller = derniere_log(nhm2_exec_path)

            restart_program()
        break


    detached_handle = handle.Detach()
    file_descriptor = msvcrt.open_osfhandle(detached_handle, os.O_RDONLY)
    with open(file_descriptor) as in_file:
        # d'abord on recherche l 'occurence dans tout le fichier, au cas ou...
        #
        #
        for line in in_file:
            match = line_regex.search(str(line))
            if match:
                # c'est qu'on a un match
                retourPid = search_and_destroy(processus_a_recuperer)
                # print(retourPid)
                logging.debug(maLigne)
                if retourPid:
                    logging.debug("killed %s", retourPid)
                else:
                    logging.debug("Processus non trouve...")

        # on a pas trouve le match, on continue

        # on va au bout du fichier
        in_file.seek(0, 2)
        #print("fichier : ", theFile)
        while not in_file.closed:
            #print(datetime.datetime.now(),"=> On lit la ligne...")
            line = in_file.readline()
            # print(line)


            if not line:
                #print(datetime.datetime.now(),"=> Rien trouve ....")
                compteur2+=1
                widgets = ['On attends 5 secs...  ',progressbar.AnimatedMarker(markers='.oO@* ')]

                # progress bar (timer de 5 secs)

                bar = progressbar.ProgressBar(widgets=widgets)

                for i in bar((i for i in range(50))):
                    time.sleep(0.1)

                # Si on a passe plus de 50 secondes et qu'il n'y a rien dans le fichier
                # on tente une reouverture du dernier fichier log

                if compteur2 >=10:
                    print(datetime.datetime.now(),"=> Ca fait trop longtemps qu il n y a rien .... On ferme et on reouvre")
                    in_file.close()
                    try:
                        win32file.CloseHandle(file_descriptor)
                    except pywintypes.error:
                        print("Erreur : le fichier a bouge")

                    yield ("vide")
                continue
            in_file.close()
            yield line


def search_and_destroy(name):
    "recupere et kill un processus 'name'. (attention qu'il soit unique)"
    assert name, name
    # ls = []
    print(datetime.datetime.now(),"=> ",name)

    # on recupere les noms des processus

    for p in psutil.process_iter():
        name_, exe, cmdline = "", "", []
        try:
            name_ = p.name()

        except (psutil.AccessDenied, psutil.ZombieProcess):
            pass
        except psutil.NoSuchProcess:
            continue

        if name == name_ or os.path.basename(exe) == name:
            procpid = p.pid
            print(datetime.datetime.now(),"=> TROUVE... on kill")
            p.kill()
            return (procpid)


logging.basicConfig(filename="./surveillance_nicehash.log", level=logging.DEBUG, format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')

# with open(output_filename, "w") as out_file:
#    out_file.write("")
log_a_surveiller = derniere_log(nhm2_exec_path)
# with open(output_filename, "a") as out_file:
compteur=0
while True:
    for maLigne in tail(log_a_surveiller):
        compteur+=1
        if (line_regex.search(str(maLigne))):
            print(maLigne)

            # out_file.write(maLigne)
            retourPid = search_and_destroy(processus_a_recuperer)
            # print(retourPid)
            logging.debug(maLigne)
            if retourPid:
                logging.debug("killed %s", retourPid)
            else:
                logging.debug("Processus non trouve...")

            # out_file.close()

        else:
            print(maLigne)

            # os.system("tasklist")
            if ((compteur%30) == 0) or (maLigne=="vide"):
                #compteur=0
                print (datetime.datetime.now(),"=> On recharge la log.")
                #print(nhm2_exec_path)
                #print (derniere_log(nhm2_exec_path))
                log_a_surveiller = derniere_log(nhm2_exec_path)

