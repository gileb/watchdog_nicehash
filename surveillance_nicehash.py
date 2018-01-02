import os
import re
import time
import psutil
import logging
import glob
import progressbar
import datetime


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


def tail(theFile):
    "equivalent de tail -f en unix"
    compteur2=0
    flag_relance=0
    with open(theFile, "r") as in_file:
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
                bar = progressbar.ProgressBar(widgets=widgets)

                for i in bar((i for i in range(50))):
                    time.sleep(0.1)
                if compteur2 >=10:
                    print(datetime.datetime.now(),"=> Ca fait trop longtemps qu il n y a rien .... On ferme et on reouvre")
                    yield("vide")
                    in_file.close()
                continue
            in_file.close()
            yield line


def search_and_destroy(name):
    "recupere et kill un processus 'name'. (attention qu'il soit unique)"
    assert name, name
    # ls = []
    print(datetime.datetime.now(),"=> ",name)
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
                log_a_surveiller = derniere_log(nhm2_exec_path)

