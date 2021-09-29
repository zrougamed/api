import traceback
from typing import Optional
from fastapi import FastAPI, Form, Response, Header, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pyTigerGraph as tg 
from datetime import date, datetime, timedelta
import jwt
import random
import re
import os 
try:
    URL = os.environ['URL']
    USER = os.environ['USER']
    PASSWORD = os.environ['PASSWORD']
    SECRET = os.environ['SECRET']
    SECRET_AUTH = os.environ['SECRET_AUTH']
    GRAPH = os.environ['GRAPH']
    GRAPH_AUTH = os.environ['GRAPH_AUTH']
except:

    from conf import URL,USER,PASSWORD,SECRET,SECRET_AUTH
    GRAPH = "synthea"
    GRAPH_AUTH = "Auth"


## uvicorn main:app --reload  --root-path /api
###### DEFINE PYTG ###########
try:
    conn = tg.TigerGraphConnection(host=URL,username=USER,password=PASSWORD,sslPort="14240",version="3.1.0")
    conn.graphname = GRAPH
    secret = conn.createSecret()
    conn.apiToken = conn.getToken(secret)
except Exception as e: 
    import time 
    print(e)
    time.sleep(1)

try:
    conn_auth = tg.TigerGraphConnection(host=URL,username=USER,password=PASSWORD,sslPort="14240",version="3.1.0")
    conn_auth.graphname = GRAPH_AUTH
    secret2 = conn_auth.createSecret()
    conn_auth.apiToken = conn_auth.getToken(secret2)
except Exception as e: 
    import time 
    print(e)
    time.sleep(10)
################################## 

app = FastAPI()
jwt_secret = "SomeStrongKey"
origins = [
    "http://c360.servehttp.com:8080",
    "http://c360.servehttp.com:8000",
    "http://localhost:8080",
    "http://localhost:8080",
    "https://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


################ HELPERS FUNCTION BLOCK ##################################



def formatter(profile):
    userProfile = {}
    userProfile['information'] = []
    userProfile['name'] = profile[0]['Name']
    # userProfile['about'] = profile[0]['Birthplace']
    picture = 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQGZGbRNgG_g82yO7ammcXwvtEUDz-0fFxM5_aUUkJoCWT9Q5VBR3cTO9QsPJ4VW1nT0ZM&usqp=CAU'
    userProfile['profile_img'] = picture
    userProfile['information'].append({"title": "Birthday","content":profile[0]['Birthday'].split(" ")[0], "type":"Birthday","icon":"fa fa-birthday-cake"})
    userProfile['information'].append({"title": "Birthplace","content":profile[0]['Birthplace'], "type":"Birthplace","icon":"fa fa-birthday-cake"})
    userProfile['information'].append({"title": "Address","content":profile[0]['@@Address'], "type":"Location","icon":"fas fa-map-marker-alt"})
    userProfile['information'].append({"title": "Gender","content":profile[0]['pGender'], "type":"Gender","icon":"fas fa-venus-mars",})
    location = profile[0]['@@Address']
    location = str(location)
    
    objE={}
    children=[]

    # for e in profile[5]['@@UserEmails']:
    #     objE={
    #         'label': e,
    #         "icon":"fas fa-envelope-square",
    #     }
    #     children.append(objE)
        
    # temp = {
    #     "type":"Email",
    #     "content":
    #         {
    #             "label":profile[0]['pGender'],
                
    #             "children":[objE]
    #         }
        
    # }
    # userProfile['information'].append(temp)
    # print(temp)
    
    userProfile['information'].append({"title": "Health Coverage","content":profile[0]['HealthcareCoverage'], "type":"HealthcareCoverage","icon":"fas fa-people-carry"})
    userProfile['information'].append({"title": "Health Expenses","content":profile[0]['HealthcareExpense'], "type":"HealthcareExpense","icon":"fas fa-hand-holding-usd"})
    userProfile['information'].append({"title": "Org.","content":profile[0]['RecentProviderOrg'], "type":"RecentProviderOrg","icon" :"fas fa-user-tie"})
    userProfile['information'].append({"title": "Recent Provider","content":profile[0]['RecentProvider'], "type":"RecentProvider","icon":"fas fa-user-tie"})
    userProfile['information'].append({"title": "Age","content":profile[0]['Age'], "type":"Age","icon":"fas fa-baby"})
    userProfile['information'].append({"title": "SSN","content":profile[0]['SSN'], "type":"SSN","icon":"fas fa-id-card"})

    if(profile[0]['pEthnicity'] != ""):
        userProfile['information'].append({"title": "Ethnicity","content":profile[0]['pEthnicity'], "type":"Discord","icon":"fas fa-fingerprint"})
    else:
        userProfile['information'].append({"title": "Ethnicity","content":'N/A', "type":"Discord","icon":"fas fa-fingerprint"})


    obj = {}
   
    return userProfile


####################### END HELPER BLOCK ##################################


def verify_token(req: Request):
    # print(req.headers)
    try:
        access_token = req.headers["Authorization"].split(" ")[1]
        try:
            access_token = access_token.split("|")[1]
        except:
            print("Not")
        # Here your code for verifying the token or whatever you use
        # print(access_token)
      
        result = conn_auth.runInstalledQuery("checkQuery",params={"access_token":access_token})
        if datetime.now() > datetime.strptime(result[0]["result"][0]["attributes"]["expiration_date"],"%Y-%m-%d %H:%M:%S"):
            raise HTTPException(
                status_code=401,
                detail= "Unauthorized"
            )
        
        return True
    except Exception as e:
        raise HTTPException(
                status_code=401,
                detail= "Unauthorized"
            )

# uvicorn main:app --reload
@app.get("/")
def read_root():
    return {"Hello": "Tigers"}

@app.post("/users/count") # Mohamed's implementation not sure do we need it ?
def getTotalUsers(authorized: bool = Depends(verify_token)):
    try:
        res = conn.runInstalledQuery("getTotalUsers")
        projectcount = conn.runInstalledQuery("getTotalProjects")
        response = [{
            "countuser": res[0]["UsersCount"],
            "countproject": projectcount[0]["RepoCount"]
        }]
        return response
    except:
        response = [{
            "countuser": "N/A",
            "countproject": "N/A"
        }]
        return  response

@app.post("/users/userProfile") # data for profile name, email, linkedin, interests...
def getPersonProfile(*, person_id: str = Form(...),authorized: bool = Depends(verify_token)):
    try:
        # Extract
        profile = conn.runInstalledQuery("patientSummary",params={"inPatient":person_id})

        # Transform
        userProfile=formatter(profile)

        response = [userProfile]
        return response
    except Exception as e:
        print("#~#############################")
        print(e)
        print(traceback.format_exc())
        print("#~#############################")
        return [{"profile_img": 'https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y',"name": '-----',"information": [
        {
          "type": "",
          "content": '',
          "icon": ''
        },
        {
          "type": "",
          "content": '',
          "icon": ''
        },
        {
          "type": "",
          "content": '',
          "icon": ''
        },
        {
          "type": "",
          "content": '',
          "icon": ''
        },
        {
          "type": "",
          "content": '',
          "icon": ''
        },
        {
          "type": "",
          "content": '',
          "icon": ''
        },
        {
          "type": "",
          "content": '',
          "icon": ''
        },
        {
          "type": "",
          "content": '',
          "icon": ''
        },
        {
          "type": "",
          "content": '',
          "icon": ''
        },
      ],"about": '---------',"isEmpty":True,"topic_interested": [],"joined_date": 'N/A',"member_for": 'N/A'}]    



    ######### tempListValid




@app.post("/users/userSummary") # data are first active, last active, interest score, engagement score
def getUserSummary(*, person_id: str = Form(...),authorized: bool = Depends(verify_token)):
    try:
        summary = conn.runInstalledQuery("patientTimeline",params={"inPatient":person_id, "inputMinDate":"1970-01-01", "inputMaxDate":date.today().strftime("%Y-%m-%d")})
        OutputTimeline = {}
        OutputTimeline = summary[2]
        currentDate = date.today().strftime('%Y-%m-%d')                                # strftime convert to string
        currentDate = datetime.strptime(currentDate,'%Y-%m-%d')                        # strptime convert to datetime
        
        OutputTimeline['firstSeen']= summary[1]['firstActive'].split(" ")[0].replace("-","/")
        
        OutputTimeline['lastSeen'] = str(((currentDate - datetime.strptime(summary[0]['lastActive'][0:10],'%Y-%m-%d')).days)) + " days ago"
        return [OutputTimeline]
    except Exception as e:
        # print(e)
        OutputTimeline = {}
        return [OutputTimeline]

@app.post("/users/userTimeline") # timeline data consist title, data, content
def getPersonTimeline(*, person_id: str = Form(...), minDate: str = Form(...), maxDate: str = Form(...),authorized: bool = Depends(verify_token)):
    try:
        timeline = conn.runInstalledQuery("patientTimeline",params={"inPatient":person_id, "inputMinDate":minDate, "inputMaxDate":maxDate})
        OutputTimeline  = []
        for element in timeline[2]["@@outputDesc"]:
            daysTemp = (datetime.now() - datetime.strptime(element["dt"][0:10], "%Y-%m-%d")).days
            daysTemp = str(daysTemp)
            if(daysTemp == 1):
                daysTemp = element["dt"][0:10].replace("-","/") #+ " (" + daysTemp + " day ago )"
            else:
                daysTemp = element["dt"][0:10].replace("-","/") #+ " (" + daysTemp + " days ago )" 
            
            icon = ""
            
            if element["source"] == 'Birthday':
                icon = 'https://cdn-icons-png.flaticon.com/512/3159/3159408.png'
            elif element["source"] == 'Observation':
                icon = 'https://cdn-icons-png.flaticon.com/512/2196/2196220.png'
            elif element["source"] == 'Encounter':
                icon = "https://cdn-icons-png.flaticon.com/512/3232/3232944.png"
            elif element["source"] == 'Condition':
                icon = "https://cdn-icons-png.flaticon.com/512/4005/4005669.png"
            elif element["source"] == "Immunization":
                icon = "https://cdn-icons-png.flaticon.com/512/2257/2257480.png"
            obj = {
                "title": element["title"],
                "content": element["content"],
                "time_passed": daysTemp, # format regardin -x days 
                "activity_source": element["source"],
                "icon": icon,
                "filter": element["dt"][0:10],
            }
            OutputTimeline.append(obj)
        return  sorted(OutputTimeline, key=lambda k: k['filter'],reverse=True) 
    except:
        return []

@app.post("/users/userActivities") # activity data is the scatter chart version
def getUserActivities(*, person_id: str = Form(...), minDate: str = Form(...), maxDate: str = Form(...),authorized: bool = Depends(verify_token)):
    try:
        activites = conn.runInstalledQuery("patientTimeline",params={"inPatient":person_id, "inputMinDate":minDate, "inputMaxDate":maxDate})
        response = {}
        if(len(activites[2]['@@outputDesc']) == 0):
            response['isEmpty'] = True
        
        response['isEmpty'] = False
        minDate = datetime.strptime(minDate,'%Y-%m-%d')
        maxDate = datetime.strptime(maxDate,'%Y-%m-%d')
        duration = (maxDate - minDate).days

        response['dates'] = []
        for x in range(duration):
            minDate += timedelta(days=1)
            # strDate = minDate.strftime('%b %d')
            strDate = minDate.strftime('%Y-%m-%d')
            response['dates'].append(strDate)





        response['sources'] = ['Birthday','Observation', 'Encounter', 'Condition']
        response['data'] = []
        
        rows, cols = (len(response['sources']), len(response['dates']))
        for r in range (rows):
            for c in range (cols):
                response['data'].append([r,0])
        all_dates = []
        temp_source = activites[2]['@@outputDesc']
        data2 = {}
        
        for s in temp_source:
            all_dates.append(s['dt'].split(" ")[0])
            temp_dt = s['dt'].split(" ")[0]
            # dt_str = temp_dt.strftime('%b %d')   
            # dt_key = dt_str+s['source']
            dt_key = temp_dt+s['source']
            data2[dt_key] = data2.get(dt_key,0)+1
        # 2D Array Data
        src_idx, dt_idx = 0, 0
        all_keys = data2.keys()
        for i in range(rows):
            for k in all_keys: 
                if response['sources'][i] in k:
                    src_idx = i
                    for j in range(cols):
                        
                        if response['dates'][j] in k:
                            dt_idx = j
                            
                            response['data'][src_idx*cols+dt_idx] = [src_idx,data2[k]]
        response["AllDates"] = all_dates
        return response
    except Exception as e:
       
        response = {}
        response["AllDates"] = []
        response['dates'] = []    
        response['data'] = []
        response['sources'] = []
        response["isEmpty"] = True
        print(e)
        print(traceback.format_exc())
        return response
import time 
@app.post("/users/getUserActivities") # version 2 of activity data with proper time interval range
def getUserActivitiesOnlyId(*, person_id: str = Form(...),authorized: bool = Depends(verify_token)):
    try:
        start = time.time()
        res = conn.runInstalledQuery("getPatientMap",params={"inPatient":person_id})
        print(str(time.time()-start))

        start = time.time()
        UniqueDate = sorted(res[0]["@@UniqueDates"], key=lambda x: datetime.strptime(x, '%Y-%m-%d'))
        firstActive = UniqueDate[0]
        lastActive = UniqueDate[-1]
        print(str(time.time()-start))
        start = time.time()
        activites = conn.runInstalledQuery("patientTimeline",params={"inPatient":person_id, "inputMinDate":firstActive, "inputMaxDate":lastActive})
        print(str(time.time()-start))
        start = time.time()
        response = {}

        if(len(activites[2]['@@outputDesc']) == 0):
            response['isEmpty'] = True
        else:
            response['isEmpty'] = False
        
       
        minDate =  datetime.strptime(firstActive, '%Y-%m-%d') 
        maxDate = datetime.strptime(lastActive, '%Y-%m-%d')  

        duration = (maxDate - minDate).days
        print(str(time.time()-start))
        start = time.time()
        response['dates'] = []
        for x in range(duration):
            minDate += timedelta(days=1)
            # strDate = minDate.strftime('%b %d')
            strDate = minDate.strftime('%Y-%m-%d')
            response['dates'].append(strDate)
        print(str(time.time()-start))
        start = time.time()
        response['sources'] = ['Observation', 'Encounter', 'Condition','Immunization']
        response['data'] = []
        
        rows, cols = (len(response['sources']), len(response['dates']))
        for r in range (rows):
            response['data'].append([])
            for c in range (cols):
                response['data'][r].append(0)
        print("ll"+str(time.time()-start))
        start = time.time()
        response["AllDates"]  = res[0]["@@AllDates"]
        print("l"+str(time.time()-start))
        start = time.time()
        temp_source = activites[2]['@@outputDesc']
        print("aaq"+str(time.time()-start))
        start = time.time()
        data2 = {}
        for s in temp_source:
            # all_dates.append(s['dt'].split(" ")[0])
            temp_dt = s['dt'].split(" ")[0]
            dt_key = temp_dt+s['source']
            data2[dt_key] = data2.get(dt_key,0)+1
        print("se"+str(time.time()-start))
        start = time.time()
        # 2D Array Data
        src_idx, dt_idx = 0, 0
        all_keys = data2.keys()
        for i in range(rows):
            for k in all_keys: 
                if response['sources'][i] in k:
                    src_idx = i
                    for j in range(cols):
                        
                        if response['dates'][j] in k:
                            dt_idx = j
                            # print(data2[k])
                            response['data'][src_idx][dt_idx] = data2[k]
        print("dd"+str(time.time()-start))
        start = time.time()
        # response["AllDates"] = all_dates
        
        
        return response
    except Exception as e:
        response = {}
        response["AllDates"] = []
        response['dates'] = []    
        response['data'] = []
        response['sources'] = []
        response["isEmpty"] = True
        print(e)
        print(traceback.format_exc())
        return response     
@app.post("/providers/membersData") # member table list
def getMembersData(authorized: bool = Depends(verify_token)):
    response = []
    try:
        memebrList = conn.runInstalledQuery("providerTable")
        memebrList = memebrList[0]['@@output']

        object = {}
        
        for element in memebrList:

            picture =  'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQGZGbRNgG_g82yO7ammcXwvtEUDz-0fFxM5_aUUkJoCWT9Q5VBR3cTO9QsPJ4VW1nT0ZM&usqp=CAU'
            

            object = {
                "id": element['ID'],
                # "name_image": [element['Name'], element['Picture']],
                "name_image": [element['Name'], picture],
                "organization": element['Organization'],
                "specialty": element['Specialty'],
                "gender": element['Gender'],
                "encounters": element['Encounters'],
                "city": element['City'],
            }
            response.append(object)
        return response
    except Exception as e:
        print(e)
        return []


@app.post("/users/membersData") # member table list
def getMembersData(authorized: bool = Depends(verify_token)):
    response = []
    try:
        memebrList = conn.runInstalledQuery("patientTable")
        memebrList = memebrList[0]['@@output']

        object = {}
        
        for element in memebrList:

            picture =  'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQGZGbRNgG_g82yO7ammcXwvtEUDz-0fFxM5_aUUkJoCWT9Q5VBR3cTO9QsPJ4VW1nT0ZM&usqp=CAU'
            

            object = {
                "id": element['ID'],
                # "name_image": [element['Name'], element['Picture']],
                "name_image": [element['Name'], picture],
                "SSN": element['SSN'],
                "Age": element['Age'],
                "Race": element['Race'],
                "Gender": element['Gender'],
                "MaritalStatus": element['MaritalStatus'],
                "HealthcareExpense": element['HealthcareExpense'],
                "HealthcareCoverage": element['HealthcareCoverage'],
            }
            response.append(object)
        return response
    except Exception as e:
        print(e)
        return []


@app.post("/users/searchMembersData") # search bar
def getSearchMemeber(authorized: bool = Depends(verify_token)):
    try:
        response = []
        memebrList = conn.runInstalledQuery("patientTable")
        memebrList = memebrList[0]['@@output']

        object = {}
        
        for element in memebrList:

            object = {
                "id": element['ID'],
                "label": element['Name'],
                # "profile_img": element['Picture'],
                "profile_img":  'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQGZGbRNgG_g82yO7ammcXwvtEUDz-0fFxM5_aUUkJoCWT9Q5VBR3cTO9QsPJ4VW1nT0ZM&usqp=CAU',
            }
            response.append(object)
        # print(response)
        return response
    except Exception as e:
        print(e)
        return []

@app.post("/users/updateAttributes")   # @Mohamed finish working on the Functions , Discord , Twitter ,  Location 
def updateAttr(*, person_id: str = Form(...), object: str=Form(...), value: str=Form(...),authorized: bool = Depends(verify_token)):
    return value
    # if object == "Discord":
    #     # call discord account insertion 
    #     pass
    # elif object == "twitter":
    #     pass 
    
@app.post("/users/updateComplexAttributes")   # @Mohamed finish working on the Functions , Discord , Twitter ,  Location 
def updateAttr(*, person_id: str = Form(...), object: str=Form(...), value: str=Form(...),authorized: bool = Depends(verify_token)):
    return value
    # if object == "Discord":
    #     # call discord account insertion 
    #     pass
    # elif object == "twitter":
    #     pass 

@app.post("/users/editOneUser")
def editFrom(*, person_id: str = Form(...), name: str = Form(...), pronouns: str = Form(...), company: str = Form(...), title: str = Form(...), city: str = Form(...), country: str = Form(...) , bio: str = Form(...), linkedin: str = Form(...),authorized: bool = Depends(verify_token)):
    try:


        
        name = name.strip('\"')
        name = name.replace("+", " ")
        pronouns = pronouns.strip('\"')
        company = company.strip('\"')
        title = title.strip('\"')
        city = city.strip('\"')
        country = country.strip('\"')
        bio = bio.strip('\"')
        linkedin = linkedin.strip('\"')

        conn.runInstalledQuery("editName", params={"inPerson":person_id, "argument":name})
        conn.runInstalledQuery("editPronouns", params={"inPerson":person_id, "argument":pronouns})

        conn.runInstalledQuery("editCompany", params={"inPerson":person_id, "argument":company})
        conn.runInstalledQuery("editPosition", params={"inPerson":person_id, "argument":title})

        conn.runInstalledQuery("editCity", params={"inPerson":person_id, "argument":city})
        conn.runInstalledQuery("editCountry", params={"inPerson":person_id, "argument":country})
        conn.runInstalledQuery("linkLocations", params={"inPerson":person_id})


        conn.runInstalledQuery("editNotes", params={"inPerson":person_id, "argument":bio})
        conn.runInstalledQuery("editLinkedIn", params={"inPerson":person_id, "argument":linkedin})

        

        # Extract
        profile = conn.runInstalledQuery("getPersonSummary",params={"inPerson":person_id})
        # Transform
        userProfile = {}
        userProfile['information'] = []
        userProfile['name'] = profile[0]['UserName']
        userProfile['about'] = profile[1]['UserNotes']
        userProfile['profile_img'] = profile[2]['UserPicture']
        userProfile['information'].append({"content":profile[3]['UserPronouns'], "type":"Pronouns","icon":"fas fa-id-card"})
        userProfile['information'].append({"content":profile[4]['@@UserLocation'], "type":"Location","icon":"fas fa-map-marker-alt"})
        location = profile[4]['@@UserLocation']
        location = str(location)
        # temp1 = location.split(', ')[0]
        # temp2 = location.split(', ')[1]
        # userProfile['city'] = temp1
        # userProfile['country'] = temp2

        # userProfile['information'].append({"content":profile[5]['@@UserEmails'], "type":"Email","icon":"fas fa-envelope-square"})
        objE={}
        children=[]

        for e in profile[5]['@@UserEmails']:
            objE={
                'label': e,
                "icon":"fas fa-envelope-square",
            }
            children.append(objE)
            
        temp = {
            "type":"Email",
            "content":[
                {
                    "label":profile[14]['UserTargetEmail'],
                    "icon":"fas fa-envelope-square",
                    "children":[objE]
                }
            ]
        }
        userProfile['information'].append(temp)

        
        userProfile['information'].append({"content":profile[6]['UserCompany'], "type":"Company","icon":"fas fa-suitcase"})
        userProfile['information'].append({"content":profile[7]['UserPosition'], "type":"Title","icon":"fas fa-user-tie"})
        userProfile['information'].append({"content":profile[8]['UserLinkedIn'], "type":"Linkedin","icon" :"fab fa-linkedin-in"})
        userProfile['information'].append({"content":profile[9]['UserTwitter'], "type":"Twitter","icon":"fab fa-twitter-square"})
        userProfile['information'].append({"content":profile[10]['UserGitHub'], "type":"Github","icon":"fab fa-github-square"})
        userProfile['information'].append({"content":'https://discordapp.com/users/'+profile[11]['UserDiscord']+'/', "type":"Discord","icon":"fab fa-discord"})

        if(profile[3]['UserPronouns'] == "" and profile[4]['@@UserLocation']== "" and profile[5]['@@UserEmails'] == "" and profile[6]['UserCompany'] == "" and profile[7]['UserPosition'] == "" and profile[8]['UserLinkedIn'] == "" and profile[9]['UserTwitter'] == "" and profile[10]['UserGitHub'] =="" and profile[11]['UserDiscord'] == ""):
            userProfile['isEmpty'] = True
        
        userProfile['isEmpty'] = False

        #20 colors
        cIndex = 0
        colors = [ "#f3722c",   "#f9c74f",  "#7d7abc", "#e3924f","#90be6d",   "#577590", "#277da1", "#575980", "#f2db80", "#e57361","#f8961e", "#c2a05b", "#d9d3d3", "#43aa8b","#52a156", "#549aa8","#4d908e","#f9844a","#f94144", "#d199cb"]
        oneColor = colors[cIndex]

        interests =  profile[13]['@@UserInterestMap'] # TODO data query can improve
        obj = {}
        interestList = []
        fullRate = 100
        i = 1
        for topic, rate in interests.items():
            fullRate -= (int(float(rate)*100))
            rs = (int(float(rate)*100))
            if(fullRate < 100):
                r1 = random.randint(0,255)
                r2 = random.randint(0,255)
                r3 = random.randint(0,255)
                
                dimension = str(rs)
                colorCode = str(r1) + ", " + str(r2) + ", " + str(r3)
                colorCode = oneColor
                colorValue  = "color: " + colorCode 
                stValue = colorValue + "; background-color: "  + colorCode + "; height: 20px; fontSize: 1px;width: " + dimension+"%"
                if(i == 1):
                    i+=1
                    stValue = colorValue + "; background-color: " + colorCode + "; height: 20px; fontSize: 1px;width: " + dimension+"%"+";border-bottom-left-radius: 25px;border-top-left-radius: 25px;"
                obj = {
                    "topic": topic,
                    "styleText":stValue,
                    "width": dimension+"%",
                    "color": colorValue
                }
                cIndex+=1
                oneColor = colors[cIndex]
                interestList.append(obj)
                # print(obj)

        if(fullRate > 0):
            # print("Working ")
            r1 = random.randint(0,255)
            r2 = random.randint(0,255)
            r3 = random.randint(0,255)
            dimension = str(fullRate)
            colorCode = str(r1) + ", " + str(r2) + ", " + str(r3)
            colorCode = oneColor
            colorValue  = "color: " + colorCode 
            stValue = colorValue + "; background-color: " +  colorCode + "; height: 20px; fontSize: 1px;width: " + dimension+"%" + ";border-bottom-right-radius: 25px;border-top-right-radius: 25px;"
            if(fullRate == 100):
                stValue = colorValue + "; background-color: " + colorCode  + "; height: 20px; fontSize: 1px;width: " + dimension+"%" + ";border-radius: 25px;"
            obj = {
                    "topic": "unspecified",
                    "styleText":stValue,
                    "width": dimension+"%",
                    "color": colorValue 
                }
            
            cIndex+=1
            oneColor = colors[cIndex]
            interestList.append(obj)
        
       

   
        # TODO need to function to transform
        userProfile['topic_interested'] = []
        summary = conn.runInstalledQuery("getPersonTimeline",params={"inPerson":person_id, "inputMinDate":"2021-06-19", "inputMaxDate":date.today().strftime("%Y-%m-%d")})
        userProfile['joined_date'] = 'N/A'
        userProfile['member_for'] = 'N/A'
        response = [userProfile]
        return response
    except Exception as e:
        print(e)
        return [{"profile_img": 'https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y',"name": '-----',"information": [
        {
          "type": "",
          "content": '',
          "icon": ''
        },
        {
          "type": "",
          "content": '',
          "icon": ''
        },
        {
          "type": "",
          "content": '',
          "icon": ''
        },
        {
          "type": "",
          "content": '',
          "icon": ''
        },
        {
          "type": "",
          "content": '',
          "icon": ''
        },
        {
          "type": "",
          "content": '',
          "icon": ''
        },
        {
          "type": "",
          "content": '',
          "icon": ''
        },
        {
          "type": "",
          "content": '',
          "icon": ''
        },
        {
          "type": "",
          "content": '',
          "icon": ''
        },
      ],"about": '---------',"isEmpty":True,"topic_interested": [],"joined_date": 'N/A',"member_for": 'N/A'}]
      

@app.post("/users/similarMembersData") # member table list
def getMembersData(*, person_id: str = Form(...),authorized: bool = Depends(verify_token)):
    response = []
    try:
        memebrList = conn.runInstalledQuery("patientSimilar",params={"inPatient":person_id} )
        memebrList = memebrList[0]['@@output']

        object = {}
        
        for element in memebrList:
            # eScore = 'Top ' + str(element['engagementScore'])+ ' %'
            picture = 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQGZGbRNgG_g82yO7ammcXwvtEUDz-0fFxM5_aUUkJoCWT9Q5VBR3cTO9QsPJ4VW1nT0ZM&usqp=CAU'
            object = {
                "id": element['ID'],
                # "name_image": [element['Name'], element['Picture']],
                "name_image": [element['Name'], picture],
                "Age": element['Age'],
                "Gender": element['Gender'],
                "MaritalStatus": element['MaritalStatus'],
                "Race": element['Race'],
            }
            response.append(object)
        return response
    except Exception as e:
        print(e)
        return []



@app.post("/dashboard") # Mohamed's implementation not sure do we need it ?
def getDashboard(authorized: bool = Depends(verify_token)):
    try:
        res = conn.runInstalledQuery("dashboardQuery")
        output = {}
        output["patients"] = res[0]["@@patients"]
        output["providers"] =  res[0]["@@providers"]
        output["statisticTable"] = res[0]["@@PaymentHistory"]
        print(res[0]["@@geoLoc"])
        output["geoMap"]    =[{"name":"","value":x} for x in res[0]["@@geoLoc"]]
        races = []
        for e in res[0]["@@race"]:
            races.append({"value":res[0]["@@race"][e],"name":e,"selected":False})
        output["race"] = races
        return output
    except Exception as e:
        print(e)
        return {"geoMap" : [],"patient":0,"providers":0}


@app.post("/graph") # Mohamed's implementation not sure do we need it ? ,authorized: bool = Depends(verify_token)
def getPatientGraph(*,person_id: str = Form(...),authorized: bool = Depends(verify_token)):
    try:
        res = conn.runInstalledQuery("getPatientGraph",params={"patientID":person_id})
        types = {}
        data = {}
        edges = res[0]["edges"]
        nodes = res[0]["nodes"]
        for d in edges:
            d['target'] = d.pop('targets')
        nodes.append({
            "id":person_id,
            "img":"https://cdn-icons-png.flaticon.com/512/2750/2750657.png",
            "label":"patient",
            "isLeaf": False,
            "legendType" : "patient"
            })
        return { "edges" : edges  , "nodes" : nodes}
    except Exception as e:
        print(e)
        return {}


def flatten(obj,commSizes):
    nodes = []
    output = []
    for e in obj:
        nodes.append({
            "id":e["v_id"],
            "label":e["v_type"],
            "isLeaf": False
            })
        element = {}
        element["v_id"] = e["v_id"]
        element["v_type"] = e["v_type"]
        for k in e["attributes"]:
            element[k] = e["attributes"][k]
        try:
            element["communitySize"] = commSizes[str(e["attributes"]["@label"])]
        except:
            element["communitySize"] = 0
        output.append(element)
    return output,nodes



@app.post("/community") # Mohamed's implementation not sure do we need it ? ,authorized: bool = Depends(verify_token)
def getPatientCommunity(*,vertices: str = Form(...),edges: str = Form(...)): # ,authorized: bool = Depends(verify_token)
    try:
        
        param = []
        for e in vertices.split("|"):
            param.append(("v_type",e))
        for e in edges.split("|"):
            param.append(("e_type",e))
        param.append(("max_iter",3))
        param.append(("output_limit",50))        
        res = conn.runInstalledQuery("tg_label_prop",params=param)

        table=[]
        nodes = []
        edges = []

        communitySize = res[0]['@@commSizes']
        table,nodes = flatten(res[1]["Start"],communitySize)
        # for e in res[3]["@@nod"]:
        #     print(e)
        
        #    {
        #     "@@edgeList": [
        #         {
        #             "e_type": "PATIENT_HAS_ALLERGY",
        #             "from_id": "fb8565ab-077b-45a3-87e1-ca9c46e5e92c",
        #             "from_type": "Patient",
        #             "cc": "306",
        #             "to_type": "Allergies",
        #             "directed": false,
        #             "attributes": {}
        #         },
        
        for e in res[2]["@@edgeList"]:
            edges.append({"source":e["from_id"],"label": e["e_type"],"target":e["to_id"]})
            if {"id":e["from_id"],"label":e["from_type"],"isLeaf": False} not in nodes:
                nodes.append({"id":e["from_id"],"label":e["from_type"],"isLeaf": False})
            if {"id":e["to_id"],"label":e["to_type"],"isLeaf": False} not in nodes:
                nodes.append({"id":e["to_id"],"label":e["to_type"],"isLeaf": False})
        # nodes = list(set(nodes))

        
        return {"table":table,"graph":{"nodes":nodes,"edges":edges}}
    except Exception as e:
        print(e)
        return {}




# JWT Part 
@app.post("/logout/")
async def logout(*, response: Response, access_token: str=Form(...)):
    # check token ?
    # Query check if access token is actif and access token is not expired , if it's linked to the user
    
    if access_token == "":
        response.status_code = 401
        return {"error":True,"message":"Invalid Token ..."}
    try:
        userID = jwt.decode(access_token, jwt_secret, algorithms=["HS256"])["userID"]
        if userID == "":
            response.status_code = 401
            return {"error":True,"message":"Invalid Token ..."}
    except:
        response.status_code = 401
        return {"error":True,"message":"Invalid Token ..."}
    try:
        condition = conn_auth.runInstalledQuery("checkQuery",params={"userID":userID,"access_token":access_token})
        if condition[0]["result"][0]["v_id"] != access_token or len(condition[0]["result"]) > 1:
            response.status_code = 401
            return {"error":True,"message":"Invalid Token ..."}
        else:
            try:

                conn_auth.upsertEdge("User",userID,"USER_HAS_TOKEN","AuthToken",access_token,attributes={"creation_date":datetime.today().strftime('%Y-%m-%d'),"actif":False})

            except:
                response.status_code = 406
                return {"error":True,"message":"Auth provider offline ..."}
            return {"error":False, "message":"logout succesful "}
    except:
        response.status_code = 406
        return {"error":True,"message":"Auth provider offline ..."}    
 
@app.post("/login/", status_code=200)
async def login(*, response : Response, username: str = Form(...), password: str = Form(...)):
    try:
        result = conn_auth.runInstalledQuery("loginQuery",params={"username":username,"password":password})[0]["res"]
    except Exception as e:
        print(e)
        response.status_code = 406
        return {"error":True,"message":"Auth provider offline ..."}

    try:
        if "id" in result:
            # Create Token and upsert Edge
            userID = result["id"]
            name = result["name"]
            email = result["email"] 
            access_token = jwt.encode({"id": userID,"name":name,"email":email,"timeStamp":str(datetime.now())}, jwt_secret, algorithm="HS256")
            try:
                conn_auth.upsertEdge("User",userID,"USER_HAS_TOKEN","AuthToken",access_token,attributes={"creation_date":datetime.today().strftime('%Y-%m-%d %H:%M:%S'),"actif":True})
                conn_auth.upsertVertex("AuthToken",access_token,attributes={ "expiration_date":str((datetime.now() + timedelta(minutes=60)).strftime('%Y-%m-%d %H:%M:%S'))})
            except Exception as e:
                print(e)
                response.status_code = 406
                return {"error":True,"message":"Auth provider offline ..."}
            return {"error":False,"access_token":access_token,"name":name}
        else:
            response.status_code = 200
            return {"error":True,"message":"Access Denied ..."}
    except Exception as e:
        print(e)
        response.status_code = 406
        return {"error":True,"message":"Auth provider offline ..."}

