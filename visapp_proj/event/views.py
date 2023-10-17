from django.shortcuts import render,redirect
from django.contrib.auth.models import User
#import calendar
#from calendar import HTMLCalendar
#from datetime import datetime
#from .models import Event
from .models import Square
from .models import Beacon
from .models import genomeEntry
#from .models import MyPlayer
from .models import UserProfile
from .models import Question
import random
from random import shuffle
#from django.http import HttpResponse
#from django.http import JsonResponse
#import json
import math
from math import exp
from django.contrib.auth import authenticate, login
import string
#from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from django.conf import settings
import os
from .models import ListItem
from Bio import SeqIO

import csv
#from django.http import HttpResponse

blast_files_base_dir="D:/blastresults"
work_files_base_dir="D:/blastresults"
default_genome_dir="C:/Users/Eris/Documents/autothinktestfolder/frankiatestgenomes"

def moveallowed(startx,endx,starty,endy):
    
    p1=[int(startx),int(starty)]
    p2=[int(endx),int(endy)]
    pdist=math.dist(p1,p2)
    
    if pdist<1.5:
        endsquare = Square.objects.get(x=endx, y=endy)
        if 'land' in endsquare.image:
            return False
        return True
    return False


def help(request):
    return render(request,'event/help.html',
        {})

def home(request):
    #load_questions_from_file()
    if not request.user.is_authenticated:

            # Generate a random username and password
        username10 = ''.join(random.choice(string.ascii_letters) for _ in range(10))
        password = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))

        # Create a new user with the generated username and password
        user = User.objects.create_user(username=username10, password=password)
        question = Question.objects.filter(name='Correct_1').order_by('?').first()
        user_profile = UserProfile.objects.create(user=user,name=user,x='0',y='0',xpos=5,ypos=5,pending_xpos=0,pending_ypos=0,correct_answers=0,wrong_answers=0,question=question,user_type='temp',mode='move')
        user.userprofile=user_profile

        # Authenticate and log in the user
        user = authenticate(request, username=username10, password=password)

        # Set square to be occupied by user
        beginsquare = Square.objects.get(x=5, y=5)
        beginsquare.occupants3.add(user.userprofile)
        beginsquare.save()
        login(request, user)

    user=request.user
    grid_size_x = 15
    grid_size_y = 15

    myrange_x=range(user.userprofile.x,int(user.userprofile.x)+grid_size_x)
    myrange_y=range(user.userprofile.y,int(user.userprofile.y)+grid_size_y)

    startx = int(user.userprofile.x)
    stopx = int(user.userprofile.x)+grid_size_x
    starty = int(user.userprofile.y)
    stopy = int(user.userprofile.y)+grid_size_y

    charsx = [str(i) for i in range(startx, stopx)]
    charsy = [str(i) for i in range(starty, stopy)]

    currentdir=""
    currendir_listing=[]

    try:
        question = user.userprofile.question
    except:
        question = Question.objects.exclude(area1='utility').filter(difficulty__lte=3).order_by('?').first()

    answers = [question.answer1_swedish, question.answer2_swedish, question.answer3_swedish, question.answer4_swedish]

    if request.method == 'POST':
        sent_action = request.POST.get('command')
        sent_answer = request.POST.get('answer')

        print("sent action")
        print(sent_action)


        if sent_action == 'answer':
            right_answer=user.userprofile.question.answer1_swedish
            ############################
            # Correct answer
            ############################
            if right_answer == sent_answer:

                # increment right answers
                user.userprofile.correct_answers+=1

                # delete from starting square
                startsquare = Square.objects.get(y=str(user.userprofile.ypos),x=str(user.userprofile.xpos))
                startsquare.occupants3.remove(user.userprofile)
                startsquare.save()

                # add userprofile to end square
                endsquare = Square.objects.get(x=user.userprofile.pending_xpos, y=user.userprofile.pending_ypos)
                endsquare.occupants3.add(user.userprofile)
                endsquare.save()
                
                # get moved direction
                movedx,movedy=getmovedir(user.userprofile.xpos,user.userprofile.ypos,user.userprofile.pending_xpos,user.userprofile.pending_ypos)

                # set new userprofile coordinates
                user.userprofile.xpos=user.userprofile.pending_xpos
                user.userprofile.ypos=user.userprofile.pending_ypos
                user.userprofile.pending_xpos=0
                user.userprofile.pending_ypos=0
                user.userprofile.save()

                # adjust view
                
                if movedx==1:
                    temp=user.userprofile.x
                    user.userprofile.x=temp+1
                    user.userprofile.save()
                   
                if movedx==-1:
                    temp=user.userprofile.x
                    user.userprofile.x=temp-1
                    user.userprofile.save()
                if movedy==-1:
                    temp=user.userprofile.y
                    user.userprofile.y=temp-1
                    user.userprofile.save()
                if movedy==1:
                    temp=user.userprofile.y
                    user.userprofile.y=temp+1
                    user.userprofile.save()

                myrange_x,myrange_y,dbsquares=getDatabaseAndView(user.userprofile.x,user.userprofile.y,grid_size_x,grid_size_y)
                
                #set question to correct
                question = Question.objects.filter(name='Correct_1').order_by('?').first()
                user.userprofile.question=question
                user.userprofile.save()
                # there shouldnt be any answers

                answers = [question.answer1_swedish, question.answer2_swedish, question.answer3_swedish, question.answer4_swedish]
                overlays=getLabels(user,dbsquares,30)
                return render(request,'event/home.html',{'myrange_x':myrange_x,'myrange_y':myrange_y,'squaredb':dbsquares,'question':question,'answers':answers,'overlays':overlays,'currentdir':currentdir,'currentdir_listing':currendir_listing})
            print("sent_command commitdirectory")
            sent_path = request.POST.get('answer')
            print (sent_path)
            if os.path.isdir(sent_path):
                print(f"{sent_path} is a directory!")
                user.userprofile.current_genome_dir=sent_path
                currendir_listing = os.listdir(sent_path)
                user.userprofile.save()
            
                myrange_x,myrange_y,dbsquares=getDatabaseAndView(user.userprofile.x,user.userprofile.y,grid_size_x,grid_size_y)

                question = Question.objects.filter(name='Wrong_1').order_by('?').first()
                user.userprofile.question=question
                user.userprofile.save()
                answers = [question.answer1_swedish, question.answer2_swedish, question.answer3_swedish, question.answer4_swedish]
                overlays=getLabels(user,dbsquares,30)
                return render(request,'event/home.html',{'myrange_x':myrange_x,'myrange_y':myrange_y,'squaredb':dbsquares,'question':question,'answers':answers,'overlays':overlays,'currentdir':sent_path,'currentdir_listing':currendir_listing})
            



            # end of right answer
            else: #wrong answer
                print('wrog')
                user.userprofile.wrong_answers+=1
                user.userprofile.save()
                myrange_x,myrange_y,dbsquares=getDatabaseAndView(user.userprofile.x,user.userprofile.y,grid_size_x,grid_size_y)

                question = Question.objects.filter(name='Wrong_1').order_by('?').first()
                user.userprofile.question=question
                user.userprofile.save()
                answers = [question.answer1_swedish, question.answer2_swedish, question.answer3_swedish, question.answer4_swedish]
                overlays=getLabels(user,dbsquares,30)
                return render(request,'event/home.html',{'myrange_x':myrange_x,'myrange_y':myrange_y,'squaredb':dbsquares,'question':question,'answers':answers,'overlays':overlays})

            # end of wrong answer
        # end of command: answer


       

        if sent_action == 'addgenomes':
            print("sent_command addgenomes")
            sent_answer = request.POST.get('answer').split(",")
            for i in sent_answer:
                print(i)
                existing_entry = genomeEntry.objects.filter(name=i).first()

                if not existing_entry:
                    if os.path.isdir(user.userprofile.current_genome_dir+"/"+i):
                        dirinput="1"
                    else:
                        dirinput="0"
                    my_blast_files_dir=blast_files_base_dir+"/"+sent_answer
                    if not os.path.exists(my_blast_files_dir):
                        os.makedirs(my_blast_files_dir)

                    my_work_files_dir=work_files_base_dir+"/"+sent_answer
                    if not os.path.exists(my_work_files_dir):
                        os.makedirs(my_work_files_dir)
                    genomeP = genomeEntry.objects.create(name=i, path=user.userprofile.current_genome_dir, extra='sea3', is_dir=dirinput,blast_files_dir=my_blast_files_dir,work_files_dir=my_work_files_dir)



        if sent_action == 'analyzefile':
            print("sent_command analyzefile")
            sent_answer = request.POST.get('answer')
         
            genObj = genomeEntry.objects.filter(name=sent_answer).first()
           
            genomeFullPath=genObj.path+"/"+genObj.name
            contigs=getGenomeInfo(genomeFullPath)
            print(contigs[0])
            print(contigs[1])
            genObj.contigs_num=contigs[0]
            genObj.genome_size=contigs[1]
            genObj.save()
            answers = [question.answer1_swedish, question.answer2_swedish, question.answer3_swedish, question.answer4_swedish]
            myrange_x,myrange_y,dbsquares=getDatabaseAndView(user.userprofile.x,user.userprofile.y,grid_size_x,grid_size_y)
            overlays=getLabels(user,dbsquares,30)
            sent_path=user.userprofile.current_genome_dir
            return render(request,'event/home.html',{'myrange_x':myrange_x,'myrange_y':myrange_y,'squaredb':dbsquares,'question':question,'answers':answers,'overlays':overlays,'currentdir':sent_path,'currentdir_listing':currendir_listing})



        if sent_action == 'prepare':
            print("sent_command prepare")
            sent_answer = request.POST.get('answer')
         
            genObj = genomeEntry.objects.filter(name=sent_answer).first()
           
            genomeFullPath=genObj.path+"/"+genObj.name
            contigs=prepareGenomeForBlast(genomeFullPath)
            print(contigs[0])
            print(contigs[1])
            genObj.contigs_num=contigs[0]
            genObj.genome_size=contigs[1]
            genObj.save()


            
            answers = [question.answer1_swedish, question.answer2_swedish, question.answer3_swedish, question.answer4_swedish]
            myrange_x,myrange_y,dbsquares=getDatabaseAndView(user.userprofile.x,user.userprofile.y,grid_size_x,grid_size_y)
            overlays=getLabels(user,dbsquares,30)
            sent_path=user.userprofile.current_genome_dir
            return render(request,'event/home.html',{'myrange_x':myrange_x,'myrange_y':myrange_y,'squaredb':dbsquares,'question':question,'answers':answers,'overlays':overlays,'currentdir':sent_path,'currentdir_listing':currendir_listing})



        if sent_action == 'commitDirectory':
            print("sent_command commitdirectory")
            sent_path = request.POST.get('answer')
            print (sent_path)
            if os.path.isdir(sent_path):
                print(f"{sent_path} is a directory!")
                user.userprofile.current_genome_dir=sent_path
                currendir_listing = os.listdir(sent_path)
                user.userprofile.save()
            
                myrange_x,myrange_y,dbsquares=getDatabaseAndView(user.userprofile.x,user.userprofile.y,grid_size_x,grid_size_y)

                question = Question.objects.filter(name='Wrong_1').order_by('?').first()
                user.userprofile.question=question
                user.userprofile.save()
                answers = [question.answer1_swedish, question.answer2_swedish, question.answer3_swedish, question.answer4_swedish]
                overlays=getLabels(user,dbsquares,30)
                return render(request,'event/home.html',{'myrange_x':myrange_x,'myrange_y':myrange_y,'squaredb':dbsquares,'question':question,'answers':answers,'overlays':overlays,'currentdir':sent_path,'currentdir_listing':currendir_listing})

            


        
        print("here------------------------")
        file_list = ["test1","testt2"]#os.listdir(directory_path)
    
        items = []
        for file_name in file_list:
            item = ListItem(name=file_name)
            items.append(item)
            print(file_name)


        # Send ranges,database,question and randomly ordered answers
        myrange_x,myrange_y,dbsquares=getDatabaseAndView(user.userprofile.x,user.userprofile.y,grid_size_x,grid_size_y)
        overlays=getLabels(user,dbsquares,30)
        sent_path=user.userprofile.current_genome_dir
        #return render(request,'event/home.html',{'myrange_x':myrange_x,'myrange_y':myrange_y,'squaredb':dbsquares,'question':question,'answers':answers,'overlays':overlays})
        return render(request,'event/home.html',{'myrange_x':myrange_x,'myrange_y':myrange_y,'squaredb':dbsquares,'question':question,'answers':answers,'overlays':overlays,'currentdir':sent_path,'currentdir_listing':currendir_listing})

    # end of if request was post


    else: # if request method was not post

        #dbsquares = Square.objects.filter(x__in=charsx,y__in=charsy)
        myrange_x,myrange_y,dbsquares=getDatabaseAndView(user.userprofile.x,user.userprofile.y,grid_size_x,grid_size_y)

        # Send ranges,database,question and randomly ordered answers
        overlays=getLabels(user,dbsquares,30)

        directory_path = 'C:/Users/Eris/Documents'  # Replace with the path to your directory
        print("here------------------------")
        file_list = ["test1","testt2"]#os.listdir(directory_path)
    
        items = []
        for file_name in file_list:
            item = ListItem(name=file_name)
            items.append(item)
 

        #items = ListItem.objects.all()
        sent_path=user.userprofile.current_genome_dir
        return render(request,'event/home.html',{'myrange_x':myrange_x,'myrange_y':myrange_y,'squaredb':dbsquares,'question':question,'answers':answers,'overlays':overlays,'currentdir':sent_path,'currentdir_listing':currendir_listing})


def getGenomeInfo(genomeFullPath):
    file_end=genomeFullPath.split(".")[-1]
    genbank_endings= ["gbk", "gb","gbff"]
    fasta_endings= ["fa", "fasta","fna"]
    genomeFullPath_fh=open(genomeFullPath,"r")
    print(file_end)
    if file_end in genbank_endings:
        parsed_genbank=list(SeqIO.parse(genomeFullPath_fh,"genbank"))
        print("genbank")
    elif file_end in fasta_endings:
        print("fasta")
        parsed_genbank=list(SeqIO.parse(genomeFullPath_fh,"fasta"))
    else:
        print("error")

    genomeFullPath_fh.close()
    numcontigs=len(parsed_genbank)
    totalgenomesize=0
    for record in parsed_genbank:
        seq= str(record.seq)
        seqlen=len(seq)
        totalgenomesize+=seqlen

    print(dir(parsed_genbank))
    return(numcontigs,totalgenomesize)

def prepareGenomeForBlast(genomeFullPath):
    file_end=genomeFullPath.split(".")[-1]
    genbank_endings= ["gbk", "gb","gbff"]
    fasta_endings= ["fa", "fasta","fna"]
    genomeFullPath_fh=open(genomeFullPath,"r")
    print(file_end)
    if file_end in genbank_endings:
        parsed_genbank=list(SeqIO.parse(genomeFullPath_fh,"genbank"))
        print("genbank")
    elif file_end in fasta_endings:
        print("fasta")
        parsed_genbank=list(SeqIO.parse(genomeFullPath_fh,"fasta"))
    else:
        print("error")

    genomeFullPath_fh.close()
    numcontigs=len(parsed_genbank)
    totalgenomesize=0
    for record in parsed_genbank:
        seq= str(record.seq)
        seqlen=len(seq)
        totalgenomesize+=seqlen

    print(dir(parsed_genbank))
    return(numcontigs,totalgenomesize)




def getmovedir(xstart,ystart,xend,yend):
    dx=int(int(xend)-int(xstart))
    dy=int(yend-ystart)
    return (dx,dy)

def delete_inactive_temp_users():
    threshold = timezone.now() - timedelta(minutes=10)
    inactive_users = User.objects.filter(userprofile__user_type='temp', userprofile__last_active_time__lt=threshold)
    inactive_users.delete()

def getDatabaseAndView(userx,usery,gridx,gridy):

    dbsquares = genomeEntry.objects.all()
    for i in dbsquares:
        print(i.name)
    myrange_x=range(userx,int(userx)+gridx)
    myrange_y=range(usery,int(usery)+gridy)

    return (myrange_x,myrange_y,dbsquares)


def getDatabaseAndView3(userx,usery,gridx,gridy):
    myrange_x=range(userx,int(userx)+gridx)
    myrange_y=range(usery,int(usery)+gridy)

    startx = int(userx)
    stopx = int(userx)+gridx
    starty = int(usery)
    stopy = int(usery)+gridy

    charsx = [str(i) for i in range(startx, stopx)]
    charsy = [str(i) for i in range(starty, stopy)]
    dbsquares = Square.objects.filter(x__in=charsx,y__in=charsy)

    return (myrange_x,myrange_y,dbsquares)

def getLabels(user,gottendata,squaresize):


    #testsquare=Square.objects.filter(x='5',y='5').first()
    #testsquare.map_label="Start"
    #testsquare.save()

    #testsquare2=Square.objects.filter(x='10',y='5').first()
    #testsquare2.map_label="Vardagens Hav"
    #testsquare2.save()



    returnArray=[]



    return returnArray

def editmap(request):
    user=request.user
    grid_size_x = 21
    grid_size_y = 21

    myrange_x=range(user.userprofile.x,int(user.userprofile.x)+grid_size_x)
    myrange_y=range(user.userprofile.y,int(user.userprofile.y)+grid_size_y)

    startx = int(user.userprofile.x)
    stopx = int(user.userprofile.x)+grid_size_x
    starty = int(user.userprofile.y)
    stopy = int(user.userprofile.y)+grid_size_y

    charsx = [str(i) for i in range(startx, stopx)]
    charsy = [str(i) for i in range(starty, stopy)]

    try:
        question = user.userprofile.question
    except:
        question = Question.objects.exclude(area1='utility').filter(difficulty__lte=3).order_by('?').first()

    answers = [question.answer1_swedish, question.answer2_swedish, question.answer3_swedish, question.answer4_swedish]

    if request.method == 'POST':
        sent_action = request.POST.get('command')
        sent_answer = request.POST.get('answer')
        

        if sent_action == 'commitDirectory':
            print("sent_command commitdirectory")
            sent_path = request.POST.get('answer')
            print (sent_path)
            if os.path.isdir(sent_path):
                print(f"{sent_path} is a directory!")
                user.userprofile.current_genome_dir=sent_path
                currendir_listing = os.listdir(sent_path)
                user.userprofile.save()
            
                myrange_x,myrange_y,dbsquares=getDatabaseAndView(user.userprofile.x,user.userprofile.y,grid_size_x,grid_size_y)

                question = Question.objects.filter(name='Wrong_1').order_by('?').first()
                user.userprofile.question=question
                user.userprofile.save()
                answers = [question.answer1_swedish, question.answer2_swedish, question.answer3_swedish, question.answer4_swedish]
                overlays=getLabels(user,dbsquares,30)
                return render(request,'event/home.html',{'myrange_x':myrange_x,'myrange_y':myrange_y,'squaredb':dbsquares,'question':question,'answers':answers,'overlays':overlays,'currentdir':sent_path,'currentdir_listing':currendir_listing})



        if sent_action == 'move_view':
            sent_x = request.POST.get('sent_x')
            sent_y = request.POST.get('sent_y')
            temp=user.userprofile.x
            user.userprofile.x=temp+int(sent_x)
            temp=user.userprofile.y
            user.userprofile.y=temp+int(sent_y)
            user.userprofile.save()

            myrange_x,myrange_y,dbsquares=getDatabaseAndView(user.userprofile.x,user.userprofile.y,grid_size_x,grid_size_y)
            overlays=getLabels(user,dbsquares,30)
            beacons=Beacon.objects.all()
            return render(request,'event/editmap.html',{'myrange_x':myrange_x,'myrange_y':myrange_y,'squaredb':dbsquares,'question':question,'answers':answers,'overlays':overlays,'beacons':beacons})
        # end of command: move_view
        if sent_action == 'change_mode':
            sent_mode = request.POST.get('newmode')
           
            sent_beacon_area = request.POST.get('beacon_area_text')
            sent_beacon_area_s = request.POST.get('beacon_area_strength')

            try:
                label_text= request.POST.get('label_text')
                print('labeltest'+label_text)
            except:
                print('could not get label text')
            question_text= request.POST.get('question_text')
            user.userprofile.mode=sent_mode
            user.userprofile.temp_label_holder=label_text
            user.userprofile.temp_question_area_holder=sent_beacon_area
            user.userprofile.temp_question_area_strength_holder=sent_beacon_area_s
            
            user.userprofile.save()
            myrange_x,myrange_y,dbsquares=getDatabaseAndView(user.userprofile.x,user.userprofile.y,grid_size_x,grid_size_y)
            overlays=getLabels(user,dbsquares,30)
            label_text= request.POST.get('label_text')
            beacons=Beacon.objects.all()
            return render(request,'event/editmap.html',{'myrange_x':myrange_x,'myrange_y':myrange_y,'squaredb':dbsquares,'question':question,'answers':answers,'overlays':overlays,'beacons':beacons})



        # command wasnt answer, so use wants to move

        try:
            sent_x = request.POST.get('sent_x')
            print('sent x'+sent_x)
        except:
            print('could not get x')

        try:
            sent_y = request.POST.get('sent_y')
        except:
            print('could not get y')

        # User wants to move, create a question
        if user.userprofile.mode=="move":
            if moveallowed(user.userprofile.xpos,sent_x,user.userprofile.ypos,sent_y):
                question = Question.objects.exclude(area1='utility').filter(difficulty__lte=3).order_by('?').first()
                user.userprofile.pending_xpos=sent_x
                user.userprofile.pending_ypos=sent_y
                user.userprofile.question=question
                user.userprofile.save()
                #dbsquares = Square.objects.filter(x__in=charsx,y__in=charsy)

                myrange_x,myrange_y,dbsquares=getDatabaseAndView(user.userprofile.x,user.userprofile.y,grid_size_x,grid_size_y)



                answers = [question.answer1_swedish, question.answer2_swedish, question.answer3_swedish, question.answer4_swedish]
                shuffle(answers)  # shuffles the answers randomly
                user.userprofile.question=question
                user.userprofile.save()
            # end of if moveallowed
        # end of if mode move

        # User wants to paint sea
        if user.userprofile.mode=="paint sea":
            try:
                square = Square.objects.get(x=sent_x, y=sent_y)
            except Square.DoesNotExist:
                square = Square.objects.create(x=sent_x, y=sent_y, name='sea3', image='sea.png',)

        if user.userprofile.mode=="paint land":
            try:
                square = Square.objects.get(x=sent_x, y=sent_y)
            except Square.DoesNotExist:
                square = Square.objects.create(x=sent_x, y=sent_y, name='land', image='land.png',)
        if user.userprofile.mode=="delete":
            try:
                square = Square.objects.get(x=sent_x, y=sent_y)
                square.delete()
            except Square.DoesNotExist:
                print('no square at there')
        if user.userprofile.mode=="addlabel":
            try:
                square = Square.objects.get(x=sent_x, y=sent_y)
            except Square.DoesNotExist:
                print('no square at there')
                    #testsquare2=Square.objects.filter(x='10',y='5').first()
            square.map_label=user.userprofile.temp_label_holder
            square.save()

        if user.userprofile.mode=='questionarea1':
            try:
                square = Square.objects.get(x=sent_x, y=sent_y)
                print('set q in area:'+str(sent_x)+'gg'+str(sent_y))
                square.question_area1=user.userprofile.temp_label_holder
                square.save()
            except Square.DoesNotExist:
                print('no square at there')

        if user.userprofile.mode=='beacon':
            beac = Beacon.objects.create(x=sent_x, y=sent_y, name='beacon', question_area1=user.userprofile.temp_question_area_holder,question_area1_strength=user.userprofile.temp_question_area_strength_holder)
            beac.save()



              
            
        # end of if paint sea

        # Send ranges,database,question and randomly ordered answers
        myrange_x,myrange_y,dbsquares=getDatabaseAndView(user.userprofile.x,user.userprofile.y,grid_size_x,grid_size_y)
        overlays=getLabels(user,dbsquares,30)
        beacons=Beacon.objects.all()
        return render(request,'event/editmap.html',{'myrange_x':myrange_x,'myrange_y':myrange_y,'squaredb':dbsquares,'question':question,'answers':answers,'overlays':overlays,'beacons':beacons})
    # end of if request was post


    else: # if request method was not post
        print("sent_command commitdirectory")
        sent_path=user.userprofile.current_genome_dir
        if sent_path=="-1":
            sent_path=default_genome_dir
            user.userprofile.current_genome_dir=default_genome_dir
            user.save()

        if os.path.isdir(sent_path):
            currendir_listing = os.listdir(sent_path)

        myrange_x,myrange_y,dbsquares=getDatabaseAndView(user.userprofile.x,user.userprofile.y,grid_size_x,grid_size_y)

        # Send ranges,database,question and randomly ordered answers
        overlays=getLabels(user,dbsquares,30)

        directory_path = 'C:/Users/Eris/Documents'  # Replace with the path to your directory
        print("here------------------------")
        file_list = ["test1","testt2"]#os.listdir(directory_path)
    
        items = []
        for file_name in file_list:
            item = ListItem(name=file_name)
            items.append(item)


 

        #items = ListItem.objects.all()
        sent_path=user.userprofile.current_genome_dir
        return render(request,'event/home.html',{'myrange_x':myrange_x,'myrange_y':myrange_y,'squaredb':dbsquares,'question':question,'answers':answers,'overlays':overlays,'currentdir':sent_path,'currentdir_listing':currendir_listing})

def get_image_size(file_path):
    with Image.open(file_path) as img:
        width, height = img.size
    return width, height

def export_questions_to_csv():
    with open("test.csv", mode='w', encoding='UTF-16', newline='') as csv_file:


        #fieldnames = ['id', 'name','question_swedish','answer1_swedish','answer2_swedish','answer3_swedish','answer4_swedish', 'question_english','answer1_english','answer2_english','answer3_english','answer4_english','area1', 'area2', 'area3','difficulty']
        #writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer = csv.DictWriter(csv_file, fieldnames=['id', 'name', 'question_swedish', 'answer1_swedish', 'answer2_swedish', 'answer3_swedish', 'answer4_swedish', 'question_english', 'answer1_english', 'answer2_english', 'answer3_english', 'answer4_english', 'area1', 'area2', 'area3', 'difficulty'], delimiter='\t')
        writer.writeheader()

        for question in Question.objects.all():
            writer.writerow({
                'id': question.id,
                'name': question.name,
                'question_swedish': question.question_swedish,
                'answer1_swedish': question.answer1_swedish,
                'answer2_swedish': question.answer2_swedish,
                'answer3_swedish': question.answer3_swedish,
                'answer4_swedish': question.answer4_swedish,
                'question_english': question.question_english,
                'answer1_english': question.answer1_english,
                'answer2_english': question.answer2_english,
                'answer3_english': question.answer3_english,
                'answer4_english': question.answer4_english,
                'area1': question.area1,
                'area2': question.area2,
                'area3': question.area3,
                'difficulty': question.difficulty,
            })

   
    print('wrote file')


def load_questions_from_file():
    with open(f"test.csv", mode='r', encoding='UTF-16', newline='') as csv_file:
        reader = csv.DictReader(csv_file, fieldnames=['id', 'name', 'question_swedish', 'answer1_swedish', 'answer2_swedish', 'answer3_swedish', 'answer4_swedish', 'question_english', 'answer1_english', 'answer2_english', 'answer3_english', 'answer4_english', 'area1', 'area2', 'area3', 'area4', 'area5', 'difficulty'], delimiter='\t')
        # Skip header row
        next(reader)
        # Clear existing questions
        Question.objects.all().delete()
        # Load new questions from file
        for row in reader:
            Question.objects.create(
                id=row['id'],
                name=row['name'],
                question_swedish=row['question_swedish'],
                answer1_swedish=row['answer1_swedish'],
                answer2_swedish=row['answer2_swedish'],
                answer3_swedish=row['answer3_swedish'],
                answer4_swedish=row['answer4_swedish'],
                question_english=row['question_english'],
                answer1_english=row['answer1_english'],
                answer2_english=row['answer2_english'],
                answer3_english=row['answer3_english'],
                answer4_english=row['answer4_english'],
                area1=row['area1'],
                area2=row['area2'],
                area3=row['area3'],
                area4=row['area4'],
                area5=row['area5'],
                difficulty=row['difficulty'],
            )



def get_question(endsquare):
    beaconslist = find_closest_beacons(int(endsquare.x), int(endsquare.y))
    colorfractions = get_color_fractions(int(endsquare.x), int(endsquare.y), beaconslist)
    total_intensity = sum(colorfractions.values())

    random_num = random.uniform(0, total_intensity)
    print(colorfractions.items())

    for color, intensity in colorfractions.items():
        random_num -= intensity
        if random_num <= 0:
            chosen_color = color
            chosen_beacon = Beacon.objects.filter(question_area1=color).order_by('?').first()
            break

    d = distance(endsquare.x, endsquare.y, chosen_beacon.x, chosen_beacon.y)-chosen_beacon.buffer
    #difficulty = 2+round(5 * (1 / (d ** 2 + 1)))
    difficulty=get_difficulty(d)

    #random_question = Question.objects.filter(difficulty__lte=5).filter(area3=chosen_color).order_by('?').first()

    random_question = Question.objects.filter(difficulty__lte=difficulty).filter(area3=chosen_color).order_by('?').first()
    if random_question is None:
        print('wuestion was none')
        random_question = Question.objects.filter(area3=chosen_color).order_by('?').first()

    print('distance'+str(d))
    print('difficulty'+str(difficulty))
    print('kind'+str(chosen_color))
    return random_question


def find_closest_beacons(x, y):
    # Retrieve all beacons from the database
    all_beacons = Beacon.objects.all()

    # Calculate the distance between each beacon and the given position
    distances = []
    for beacon in all_beacons:
        distance = math.sqrt((beacon.x - x) ** 2 + (beacon.y - y) ** 2)
        distances.append((beacon, distance))

    # Sort the beacons based on their distance
    sorted_beacons = sorted(distances, key=lambda x: x[1])

    # Return the top five closest beacons
    closest_beacons = [beacon[0] for beacon in sorted_beacons[:5]]

    return closest_beacons

def distance(x1, y1, x2, y2):
    x1 = float(x1)
    y1 = float(y1)
    x2 = float(x2)
    y2 = float(y2)
    return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

def get_color_fractions(x, y, beacons):
    color_fractions = {}
    total_strength = 0
    for beacon in beacons:
        d = distance(x, y, beacon.x, beacon.y)
        strength = beacon.question_area1_strength * (1 / (d ** 2 + 1))
        color = beacon.question_area1
        color_fractions[color] = color_fractions.get(color, 0) + strength
        total_strength += strength
    for color in color_fractions:
        color_fractions[color] = round(color_fractions[color] / total_strength * 100, 2)
    return color_fractions

def get_difficulty(dist):
    if dist<2:
        return 5.0
    elif dist<3:
        return 4.0
    elif dist<4:
        return 3.0
    elif dist<5:
        return 2.0
    elif dist<6:
        return 1.0
    else:
        return 0.0

