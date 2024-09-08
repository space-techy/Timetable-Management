from flask import *
import mysql.connector as mysql
from flask_login import  login_user, logout_user, LoginManager, login_required, current_user
from datetime import timedelta
from user_helper import User
# from check_queries import check_data
# from api_timetable import SELECT_class,SELECT_room,SELECT_faculty
import ast
import os

#Creating instance of Flask
app = Flask(__name__)
app.secret_key = os.urandom(24)

#Flask_Login configurations to manage user login
login_manger = LoginManager()
login_manger.init_app(app)
login_manger.login_view = "login"


#LoginManager User loader
@login_manger.user_loader
def load_user(user_id):
    return User(user_id)


#Host and Other info to connect to MySQL server
#This is config to get direct access and you can change user and host and password and also database
config = {
    'host': "localhost",
    'user': "root",
    'password': "root",
    'database': "kjsce_timetable",
}


@app.before_request
def load_user():
    g.CURR_USER = session.get("username")
    g.CURR_DEPT = session.get("department")
    


#This is for users to log in
def check_data(imp_year_sem,div_para = None,all_para = None,fac_para = None,room_para = None):
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        check_div_query = f"SELECT * FROM { imp_year_sem }  WHERE class = %s AND slot = %s AND batch = %s AND division = %s AND branch = %s"
        check_all_query = f"SELECT * FROM { imp_year_sem } WHERE class = %s AND subject = %s AND slot = %s AND faculty = %s AND room = %s AND batch = %s AND branch = %s AND division = %s"
        check_fac_query = f"SELECT * FROM { imp_year_sem } WHERE slot = %s AND (faculty LIKE %s) "
        check_room_query = f"SELECT * FROM { imp_year_sem } WHERE slot = %s AND room = %s"
        if((not div_para) and (not all_para) and (not fac_para) and (room_para)):
            cursor.execute(check_room_query, room_para)
            room_res = cursor.fetchall()
            if(len(room_res) >= 1):
                return room_res
            else:
                return False
        if((not div_para) and (not all_para) and (fac_para) and (not room_para)):
            cursor.execute(check_fac_query, fac_para)
            fac_res = cursor.fetchall()
            if(len(fac_res) >= 1):
                return fac_res
            else:
                return False
        if((not div_para) and ( all_para) and (not fac_para) and (not room_para)):
            cursor.execute(check_all_query, all_para)
            all_res = cursor.fetchall()
            if(len(all_res) >= 1):
                return all_res
            else:
                return False
        if(( div_para) and (not all_para) and (not fac_para) and (not room_para)):
            cursor.execute(check_div_query, div_para)
            div_res = cursor.fetchall()
            if(len(div_res) >= 1):
                return div_res
            else:
                return False
        if(( div_para) and ( all_para) and ( fac_para) and ( room_para)):
            cursor.execute(check_div_query,div_para)
            check_div_res = cursor.fetchall()
            cursor.execute(check_all_query,all_para)
            check_all_res = cursor.fetchall()
            cursor.execute(check_fac_query,fac_para)
            check_fac_res = cursor.fetchall()
            cursor.execute(check_room_query,room_para)
            check_room_res = cursor.fetchall()
            if((len(check_div_res) > 0) or (len(check_all_res) > 0) or (len(check_fac_res) > 0) or (len(check_room_res) > 0)):
                return max(check_div_res, check_all_res,check_fac_res, check_room_res)
            else:
                return False
    finally:
        conn.close()
        
def checkSubject(imp_year_sem,branchInto,subject,batch,type_sub,division,slot_class):
    # Type checking whether there are enough lectures,practicals or tutorials available to add or not
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        sub_data_get_query = "SELECT sublecture,subtut,subprac FROM subjects WHERE subabb = %s AND subclass = %s"
        sub_data_para = (subject,slot_class)
        cursor.execute(sub_data_get_query,sub_data_para)
        sub_res = cursor.fetchall()[0]
        sub_lec,sub_tut,sub_prac = sub_res[0],sub_res[1],sub_res[2]
        print(sub_lec,sub_tut,sub_prac)
        sub_check_query = f"SELECT COUNT(type) FROM {imp_year_sem} WHERE division = %s AND batch = %s AND subject = %s AND branch = %s AND type = %s AND class = %s"
        sub_check_para_l = (division,batch,subject,branchInto,type_sub,slot_class)
        cursor.execute(sub_check_query,sub_check_para_l)
        sub_check_res = cursor.fetchall()
        print(sub_check_res)
        sub_check_res = sub_check_res[0][0]
        if("E" in type_sub):
            return False
        elif("L" in  type_sub):
            if(sub_check_res >= sub_lec):
                errorin = f"Cannot add more lectures as for this {subject} lectures quota is filled!"
                return errorin
        elif("P" in type_sub):
            if(sub_check_res >= sub_prac):
                errorin = f"Cannot add more practicals as for this {subject} practicals quota is filled!"
                return errorin
        elif("T" in type_sub):
            if(sub_check_res >= sub_tut):
                errorin = f"Cannot add more tutorials as for this {subject} tutorials quota is filled!"
                return errorin
        return False
    finally:
        conn.close()


def SELECT_class(sel_class,CURR_BRANCH,CURR_YEAR_SEM):
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        daysInDict = { "Monday" :'A' ,"Tuesday" : 'B', "Wednesday" : "C" , "Thursday": 'D', "Friday" : 'E'}
        course_year = sel_class.split(" ")[0]
        course_batch = sel_class.split(" ")[-1]
        course = " ".join(sel_class.split(" ")[1:-2])
        course_class= course_year + " " + " ".join(sel_class.split(" ")[1:-1])
        course_department = CURR_BRANCH
        div_para = (course_year, course,course_department,course_batch)
        div_query = "SELECT no_of_div FROM divisions WHERE year = %s AND course = %s AND department = %s AND batch = %s"
        cursor.execute(div_query, div_para)
        div_res = cursor.fetchall()
        if(len(div_res) == 0):
            no_of_div = 0
        else:
            no_of_div = div_res[0][0]
        time_slots = ["7:00-8:00","8:00-9:00", "9:00-10:00", "10:00-11:00", "11:00-12:00","12:00-1:00", "1:00-2:00", "2:00-3:00", "3:00-4:00", "4:00-5:00", "5:00-6:00", "6:00-7:00"]
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        # Now we are working on the part of adding colspan for days
        max_colspan_day = {"Monday": no_of_div,"Tuesday": no_of_div, "Wednesday" : no_of_div,"Thursday": no_of_div,"Friday": no_of_div}
        for t in time_slots:
            for day in days:
                max_colspan_query = f"SELECT COUNT(*) FROM {CURR_YEAR_SEM} WHERE day = %s AND time = %s AND class = %s AND division = %s"
                max_colspan_para = (day,t,course_class,course_batch)
                cursor.execute(max_colspan_query,max_colspan_para)
                max_res = cursor.fetchall()
                if(len(max_res) > 0):
                    high_than_div = max_res[0][0]
                    if(high_than_div > max_colspan_day[day]):
                        max_colspan_day[day] = high_than_div

        total_colspan = 0
        for day in days:
            total_colspan = total_colspan + max_colspan_day[day]

        # This code is for creating html table head with colspan
        table_head = "<thead><tr><th>Time/Day</th>"
        for day in days:
            table_head = table_head + f"<th colspan={max_colspan_day[day]}>{day}</th>"
        table_head  = table_head + "</tr></thead>"
        # Now we are going to create the body of the table
        check_back_row = {}
        table_body = "<tbody>"
        for t in range(len(time_slots)):
            table_body = table_body + f"<tr><td class='timeslot' style='text-align: center;'>{time_slots[t]}</td>"
            if(time_slots[t] == "1:00-2:00"):
                table_body = table_body + f'<td colspan={total_colspan} style="text-align: center;" class="lunch">LUNCH BREAK</td>'
                continue
            for day in days:
                if(time_slots[t] in check_back_row.keys()):
                    if(day in check_back_row[time_slots[t]]):
                        continue
                time_query = f"SELECT class,subject,day,faculty,room,type,branch,batch,division FROM { CURR_YEAR_SEM } WHERE day = %s AND time = %s AND branch = %s AND division = %s AND class = %s"
                curr_time_para = (day,time_slots[t],course_department, course_batch, course_class)
                cursor.execute(time_query, curr_time_para)
                curr_time_res = cursor.fetchall()
                curr_time_res = sorted(curr_time_res)
                if((t+1) != len(time_slots)):
                    next_time_para = (day,time_slots[t + 1],course_department, course_batch, course_class)
                    cursor.execute(time_query, next_time_para )
                    next_time_res = cursor.fetchall()
                    next_time_res = sorted(next_time_res)
                rowspan_or_not = False
                if(len(curr_time_res) != 0):
                    if(next_time_res and ("L" not in curr_time_res[0][5])):
                        if(curr_time_res == next_time_res):
                            if(time_slots[t+1] in check_back_row.keys()):
                                add_day =  check_back_row[time_slots[t + 1]]
                                add_day.append(day)
                                check_back_row[time_slots[t + 1]] = add_day
                                rowspan_or_not = True
                            else:
                                check_back_row[time_slots[t + 1]] = [day]
                                rowspan_or_not = True
                data_query = f"SELECT id,subject,room,faculty,division,batch,type FROM { CURR_YEAR_SEM } WHERE day = %s AND time = %s AND branch = %s AND division = %s AND class = %s"
                cursor.execute(data_query, curr_time_para)
                data_res = cursor.fetchall()

                if(len(data_res) == 0):
                    table_body = table_body + f"<td colspan = {max_colspan_day[day]} class='{daysInDict[day]+str(t+1)}'></td>"
                    continue
                what_colspan = max_colspan_day[day]//len(data_res)
                add_into_colspan = max_colspan_day[day]%len(data_res)
                colspan_dict = {}
                for i in range(len(data_res)):
                    colspan_dict[i] = what_colspan
                for i in range(add_into_colspan):
                    colspan_dict[i] = colspan_dict[i] + 1
                for curr_batch in sorted(data_res, key=(lambda x: x[5][-1])):
                    if(("E" not in curr_batch[-1]) and (curr_batch[-2] == "NO")):
                        if(rowspan_or_not):
                            td = f'<td rowspan=2 colspan={ max_colspan_day[day] } value="{curr_batch[0]}" class="{daysInDict[day]+str(t+1)}">  {" "} { curr_batch[1] } {" "} { curr_batch[2] } {" "} { curr_batch[3] }  </td>'
                            table_body = table_body + td
                        else:
                            td = f'<td rowspan=1 colspan={ max_colspan_day[day] } value="{curr_batch[0]}" class="{daysInDict[day]+str(t+1)}"> {" "} { curr_batch[1] } {" "} { curr_batch[2] } {" "} { curr_batch[3] } </td>'
                            table_body = table_body + td
                    if(("E" in curr_batch[-1]) and (curr_batch[-2] != "NO")):
                        if(rowspan_or_not):
                            colspan_val = colspan_dict[data_res.index(curr_batch)]
                            td = f"""<td rowspan=2 colspan={colspan_val} value="{curr_batch[0]}" class="{daysInDict[day]+str(t+1)}"> { curr_batch[5] } <br /> {" "} { curr_batch[2] } {" "} { curr_batch[3] } </td>"""
                            table_body = table_body + td
                        else:
                            colspan_val = colspan_dict[data_res.index(curr_batch)]
                            td = f"""<td rowspan=1 colspan={colspan_val} value="{curr_batch[0]}" class="{daysInDict[day]+str(t+1)}"> { curr_batch[5] } <br /> {" "} { curr_batch[2] } {" "} { curr_batch[3] } </td>"""
                            table_body = table_body + td

                    if(len(data_res) > 0 and ("E" in curr_batch[-1]) and (curr_batch[-2] == "NO")):
                        
                        print(curr_batch[1],curr_batch[2],curr_batch[3],curr_batch[4],curr_batch[5],curr_batch[6])
                        if(rowspan_or_not):
                            colspan_val = colspan_dict[data_res.index(curr_batch)]
                            td = f"""<td rowspan=2 colspan={colspan_val} value="{curr_batch[0]}" class="{daysInDict[day]+str(t+1)}"> {" "} { curr_batch[1] } {" "} { curr_batch[2] } {" "} { curr_batch[3] } </td>"""
                            table_body = table_body + td
                        else:
                            colspan_val = colspan_dict[data_res.index(curr_batch)]
                            td = f"""<td rowspan=1 colspan={colspan_val} value="{curr_batch[0]}" class="{daysInDict[day]+str(t+1)}"> {" "} { curr_batch[1] } {" "} { curr_batch[2] } {" "} { curr_batch[3] } </td>"""
                            table_body = table_body + td

                    if(len(data_res) > 0 and ("E" not in curr_batch[-1]) and (curr_batch[-2] != "NO")):
                        if(rowspan_or_not):
                            colspan_val = colspan_dict[data_res.index(curr_batch)]
                            td = f"""<td rowspan=2 colspan={colspan_val}  value="{curr_batch[0]}"  class="{daysInDict[day]+str(t+1)}">  { curr_batch[5] } <br /> {" "} { curr_batch[1] } {" "} { curr_batch[2] } {" "} { curr_batch[3] }  </td>"""
                            table_body = table_body + td
                        else:
                            colspan_val = colspan_dict[data_res.index(curr_batch)]
                            td = f"""<td rowspan=1 colspan={colspan_val}  value="{curr_batch[0]}"  class="{daysInDict[day]+str(t+1)}">  { curr_batch[5] } <br /> {" "} { curr_batch[1] } {" "} { curr_batch[2] } {" "} { curr_batch[3] }  </td>"""
                            table_body = table_body + td
                    next_time_res = False
            table_body = table_body + "</tr>"
        table_body = table_body + "</tbody>"
        complete_table = table_head + table_body
        return complete_table
    finally:
        conn.close()


def SELECT_room(sel_room,CURR_BRANCH,CURR_YEAR_SEM):
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        daysInDict = { "Monday" :'A' ,"Tuesday" : 'B', "Wednesday" : "C" , "Thursday": 'D', "Friday" : 'E'}
        time_slots = ["7:00-8:00","8:00-9:00", "9:00-10:00", "10:00-11:00", "11:00-12:00","12:00-1:00", "1:00-2:00", "2:00-3:00", "3:00-4:00", "4:00-5:00", "5:00-6:00", "6:00-7:00"]
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

        max_colspan_day = {"Monday": 1,"Tuesday": 1, "Wednesday" : 1,"Thursday": 1,"Friday": 1}
        for t in time_slots:
            for day in days:
                max_colspan_query = f"SELECT COUNT(*) FROM {CURR_YEAR_SEM} WHERE day = %s AND time = %s AND room LIKE %s"
                max_colspan_para = (day,t,f"%{sel_room}%")
                cursor.execute(max_colspan_query,max_colspan_para)
                max_res = cursor.fetchall()
                if(len(max_res) > 0):
                    high_than_div = max_res[0][0]
                    if(high_than_div > max_colspan_day[day]):
                        max_colspan_day[day] = high_than_div

        total_colspan = 0
        for day in days:
            total_colspan = total_colspan + max_colspan_day[day]


        table_head = "<thead><tr><th>Time/Day</th>"
        for day in days:
            table_head = table_head + f"<th colspan={max_colspan_day[day]}>{day}</th>"
        table_head = table_head + "</tr></thead>"
        check_back_row = {}
        table_body = "<tbody>"
        for t in range(len(time_slots)):
            table_body = table_body + f"<tr><td class='timeslot' style='text-align: center;'>{time_slots[t]}</td>"
            if(time_slots[t] == "1:00-2:00"):
                table_body = table_body + f'<td colspan={total_colspan} style="text-align: center;" class="lunch">LUNCH BREAK</td>'
                continue
            for day in days:
                if(time_slots[t] in check_back_row.keys()):
                    if(day in check_back_row[time_slots[t]]):
                        continue
                time_query = f"SELECT class,subject,faculty,type,division,batch FROM {CURR_YEAR_SEM} WHERE day = %s AND time = %s AND room LIKE %s"
                curr_time_para = ( day, time_slots[t],f"%{sel_room}%")
                cursor.execute(time_query, curr_time_para)
                curr_time_res = cursor.fetchall()
                curr_time_res = sorted(curr_time_res,key= lambda cur_time_res: cur_time_res[-1])
                if((t+1) != len(time_slots)):
                    next_time_para = ( day, time_slots[t+1],f"%{sel_room}%")
                    cursor.execute(time_query, next_time_para)
                    next_time_res = cursor.fetchall()
                    next_time_res = sorted(next_time_res, key= lambda next_time_res: next_time_res[-1])
                rowspan_or_not = False
                if(len(curr_time_res) != 0):
                    if(next_time_res and ("L" not in curr_time_res[0][-3])):
                        if(curr_time_res == next_time_res):
                            if(time_slots[t+1] in check_back_row.keys()):
                                add_day =  check_back_row[time_slots[t + 1]]
                                add_day.append(day)
                                check_back_row[time_slots[t + 1]] = add_day
                                rowspan_or_not = True
                            else:
                                check_back_row[time_slots[t + 1]] = [day]
                                rowspan_or_not = True  

                if(len(curr_time_res) == 0):
                    table_body = table_body + f"<td colspan={max_colspan_day[day]} class='{daysInDict[day]+str(t+1)}'></td>"
                    continue
                what_colspan = max_colspan_day[day]//len(curr_time_res)
                add_into_colspan = max_colspan_day[day]%len(curr_time_res)
                colspan_dict = {}
                for i in range(len(curr_time_res)):
                    colspan_dict[i] = what_colspan
                for i in range(add_into_colspan):
                    colspan_dict[i] = colspan_dict[i] + 1
                for curr_batch in curr_time_res:
                    colspan_val = colspan_dict[curr_time_res.index(curr_batch)]
                    if(rowspan_or_not):
                        if(curr_batch[-1] == "NO"):
                            td = f'<td value="{ sel_room }" rowspan=2 colspan={colspan_val} class="{daysInDict[day]+str(t+1)}">{ curr_batch[0] } {" "} { curr_batch[-2] } {" "}  { curr_batch[1] } {" "} { curr_batch[2] }</td>'
                            table_body = table_body + td
                        else:
                            td = f'<td value="{ sel_room }" rowspan=2 colspan={colspan_val} class="{daysInDict[day]+str(t+1)}">{ curr_batch[0] } {" "} { curr_batch[-1] } {" "}  { curr_batch[1] } {" "} { curr_batch[2] }</td>'
                            table_body = table_body + td
                    else:
                        if(curr_batch[-1] == "NO"):
                            td = f'<td value="{ sel_room }" rowspan=1 colspan={colspan_val} class="{daysInDict[day]+str(t+1)}">{ curr_batch[0] } {" "} { curr_batch[-2] } {" "}  { curr_batch[1] } {" "} { curr_batch[2] }</td>'
                            table_body = table_body + td
                        else:
                            td = f'<td value="{ sel_room }" rowspan=1 colspan={colspan_val} class="{daysInDict[day]+str(t+1)}">{ curr_batch[0] } {" "} { curr_batch[-1] } {" "}  { curr_batch[1] } {" "} { curr_batch[2] }</td>'
                            table_body = table_body + td
                next_time_res = False
            table_body = table_body + "</tr>"
        table_body = table_body + "</tbody>"
        complete_table = table_head + table_body
        return complete_table
    finally:
        conn.close()


def SELECT_faculty(sel_fac,CURR_BRANCH,CURR_YEAR_SEM):
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        daysInDict = { "Monday" :'A' ,"Tuesday" : 'B', "Wednesday" : "C" , "Thursday": 'D', "Friday" : 'E'}
        time_slots = ["7:00-8:00","8:00-9:00", "9:00-10:00", "10:00-11:00", "11:00-12:00","12:00-1:00", "1:00-2:00", "2:00-3:00", "3:00-4:00", "4:00-5:00", "5:00-6:00", "6:00-7:00"]
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

        table_head = "<thead><tr><th>Time/Day</th>"
        for day in days:
            table_head = table_head + f"<th>{day}</th>"
        table_head = table_head + "</tr></thead>"
        check_back_row = {}
        table_body = "<tbody>"
        for t in range(len(time_slots)):
            table_body = table_body + f"<tr><td class='timeslot' style='text-align: center;'>{time_slots[t]}</td>"
            if(time_slots[t] == "1:00-2:00"):
                table_body = table_body + f'<td colspan=5 style="text-align: center;" class="lunch">LUNCH BREAK</td>'
                continue
            for day in days:
                if(time_slots[t] in check_back_row.keys()):
                    if(day in check_back_row[time_slots[t]]):
                        continue
                time_query = f"SELECT class,subject,room,type,division,batch FROM  { CURR_YEAR_SEM } WHERE faculty LIKE %s AND day = %s AND time = %s"
                curr_time_para = ( f"%{sel_fac}%", day, time_slots[t], )
                cursor.execute(time_query,curr_time_para)
                curr_time_res = cursor.fetchall()
                curr_time_res = sorted(curr_time_res)
                if((t+1) != len(time_slots)):
                    next_time_para = ( f"%{sel_fac}%", day, time_slots[t+1],)
                    cursor.execute(time_query, next_time_para)
                    next_time_res = cursor.fetchall()
                    next_time_res = sorted(next_time_res)
                rowspan_or_not = False
                if(len(curr_time_res) != 0):
                    if(next_time_res and ("L" not in curr_time_res[0][-3])):
                        if(curr_time_res == next_time_res):
                            if(time_slots[t+1] in check_back_row.keys()):
                                add_day =  check_back_row[time_slots[t + 1]]
                                add_day.append(day)
                                check_back_row[time_slots[t + 1]] = add_day
                                rowspan_or_not = True
                            else:
                                check_back_row[time_slots[t + 1]] = [day]
                                rowspan_or_not = True
                if(len(curr_time_res) == 0):
                    table_body = table_body + f"<td class='{daysInDict[day]+str(t+1)}''></td>"
                    continue
                curr_batch = curr_time_res[0]
                sub_type = curr_batch[3]
                if("E" in sub_type):
                    if("NO" in curr_batch):
                        div_or_batch = curr_batch[1]
                    else:
                        div_or_batch = curr_batch[-1]
                    if(rowspan_or_not):
                        td = f'<td value="{sel_fac}" rowspan=2 class="{daysInDict[day]+str(t+1)}">{ curr_batch[0] } {" "} { div_or_batch } {" "} { curr_batch[2] }</td>'
                        table_body = table_body + td
                    else:
                        td = f'<td  value="{sel_fac}" rowspan=1 class="{daysInDict[day]+str(t+1)}">{ curr_batch[0] } {" "} { div_or_batch } {" "} { curr_batch[2] }</td>'
                        table_body = table_body + td
                elif(rowspan_or_not):
                    if(curr_batch[-1] == "NO"):
                        td = f'<td value="{sel_fac}" rowspan=2 class="{daysInDict[day]+str(t+1)}">{ curr_batch[0] } {" "} { curr_batch[-2] } {" "} { curr_batch[1] } {" "} { curr_batch[2] }</td>'
                        table_body = table_body + td
                    else:
                        td = f'<td  value="{sel_fac}" rowspan=2 class="{daysInDict[day]+str(t+1)}">{ curr_batch[0] } {" "} { curr_batch[-1] } {" "} { curr_batch[1] } {" "} { curr_batch[2] }</td>'
                        table_body = table_body + td
                else:
                    if(curr_batch[-1] == "NO"):
                        td = f'<td  value="{sel_fac}" rowspan=1 class="{daysInDict[day]+str(t+1)}">{ curr_batch[0] } {" "} { curr_batch[-2] } {" "} { curr_batch[1] } {" "} { curr_batch[2] }</td>'
                        table_body = table_body + td
                    else:
                        td = f'<td value="{sel_fac}"  rowspan=1 class="{daysInDict[day]+str(t+1)}">{ curr_batch[0] } {" "} { curr_batch[-1] } {" "} { curr_batch[1] } {" "} { curr_batch[2] }</td>'
                        table_body = table_body + td
                next_time_res = False
            table_body = table_body + "</tr>"
        table_body = table_body + "</tbody>"
        complete_table = table_head + table_body
        return complete_table
    finally:
        conn.close()


#This is for users to log in
@app.route("/login", methods=["GET","POST"], endpoint = "login")
def login_page():
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        if current_user.is_authenticated:
            return redirect("/")
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            user_info = (username,password)
            user_login = "SELECT user_id,username,user_password,department_name FROM users WHERE username = %s AND user_password = %s"
            cursor.execute(user_login,user_info)
            result = cursor.fetchall()
            if(len(result) > 0):
                user_log = User(result[0][1])
                department_name = result[0][3]
                login_user(user_log)
                session["username"] = username.upper()
                session["department"] = department_name.title()
                session.permanent = True
                app.permanent_session_lifetime = timedelta(minutes=30)
                return redirect("/")
            else:
                error = "User or Password wrong!"
                return redirect(url_for("login",error = error))
        else:
            error = request.args.get("error")
            return render_template("login.html",error = error)
    finally:
        conn.close()

#This is for users to Register
@app.route("/register", methods = ["GET", "POST"])
def register_page():
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        if current_user.is_authenticated:
            return redirect("/")
        if request.method == "POST":
            department_name = request.form.get("department_name")
            username = request.form.get("username")
            password = request.form.get("password")
            email_id = request.form.get("email_id")
            college_name = request.form.get("college_name")
            #This is to insert User Info into Database
            user_reg = "INSERT INTO users(username,email_id,user_password,college_name,department_name) VALUES (%s,%s,%s,%s,%s)"
            param = (username.upper(),email_id,password,college_name,department_name)
            try:
                cursor.execute(user_reg,param)
                conn.commit()
                #This is to fetch user id from the database to give user the access to website after logging IN
                user_id_reg = "SELECT user_id FROM users WHERE username = %s"
                cursor.execute(user_id_reg,(username,))
                cur_res = (cursor.fetchall())[0][0]
                user_res = User(cur_res)
                session["username"] = username.upper()
                session["department"] = department_name.title()
                login_user(user_res)
                return redirect("/")
            except:
                error = "User already registered! OR Some other error!"
                return render_template("register.html",error = error)

        else:
            error = request.args.get("error")
            return render_template("register.html",error = error)
    finally:
        conn.close()
    
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


# This routing is for redirecting to login page when you are on Register page
@app.route("/login_redirect", methods = ["GET"])
def login_red():
    return redirect("/login")

#This routing is for redirecting to register page if you are on login page
@app.route("/register_redirect", methods = ["GET"])
def reg_red():
    return redirect("/register")


#This route is for redirecting to our main website page after logging in
@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        if request.method == "POST":
            return render_template("main_body.html", sems_table = sems_table)
        else:
            cursor.execute("SELECT id,year,sem FROM all_timetables ORDER BY year DESC")
            sems_table = cursor.fetchall()
            return render_template("main_body.html", sems_table = sems_table)
    finally:
        conn.close()



@app.route("/create_timetable", methods=["GET", "POST"])
@login_required
def create_timetable():
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        if request.method == "POST":
            year = request.form.get("year_session")
            sem = request.form.get("sem")
            sem_year = sem + "_" + year
            session["curr_year_sem"] = sem_year
            insert_query = "INSERT INTO all_timetables( year, sem, year_sem) VALUES ( %s, %s, %s)"
            create_query = f"""CREATE TABLE {sem_year}(
                id SERIAL,
                class VARCHAR(250) NOT NULL,
                subject VARCHAR(500) NOT NULL,
                slot VARCHAR(50) NOT NULL,
                day VARCHAR(250) NOT NULL,
                time VARCHAR(250) NOT NULL,
                faculty VARCHAR(250) NOT NULL,
                room VARCHAR(250) NOT NULL,
                batch VARCHAR(200) NOT NULL,
                type VARCHAR(100) NOT NULL,
                branch VARCHAR(250) NOT NULL,
                division VARCHAR(250) NOT NULL
            )"""
            try:
                cursor.execute(insert_query, ( year, sem.upper(), sem_year))
                cursor.execute(create_query)
                conn.commit()
                return redirect("/")
            except:
                error = "TimeTable Already Exists!"
                return redirect(url_for("create_timetable",error = error))
        else:
            error = request.args.get("error")
            if(error is None):
                error = ""
            cursor.execute("SELECT id,year,sem FROM all_timetables ORDER BY year DESC")
            sems_table = cursor.fetchall()
            return render_template("main_body.html", sems_table = sems_table,error = error)
    finally:
        conn.close()

@app.route("/all_show_timetable", methods = [ "GET", "POST"])
@login_required
def edorsho():
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        if request.method == "POST":
            year_sem_id = request.form.get("year_sem_id")
            query_edit = "SELECT year_sem FROM all_timetables WHERE id = %s"
            cursor.execute(query_edit , (year_sem_id,))
            year_sem = cursor.fetchall()[0][0]
            session["curr_year_sem"] = year_sem
            return redirect ("/show_timetable")
        else:
            return redirect("/")
    finally:
        conn.close()

@app.route("/all_edit_timetable", methods = [ "GET", "POST"])
@login_required
def edtime():
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        if request.method == "POST":
            year_sem_id = request.form.get("year_sem_id")
            query_edit = "SELECT year_sem FROM all_timetables WHERE id = %s"
            cursor.execute(query_edit , (year_sem_id,))
            year_sem = cursor.fetchall()[0][0]
            session["curr_year_sem"] = year_sem
            return redirect("/assign_slots")
        else:
            return redirect("/")
    finally:
        conn.close()



@app.route("/add_subjects", methods=["GET", "POST"])
@login_required
def add_subject():
    CURR_BRANCH = session.get("username")
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        if request.method == "POST":
            sub_class = request.form.get("class_sub")
            sub_sem = request.form.get("sem")
            sub_code = request.form.get("sub_code")
            sub_abb = request.form.get("sub_abb")
            sub_name = request.form.get("sub_name")
            subL = request.form.get("total_l")
            subT = request.form.get("total_t")
            subP = request.form.get("total_p")
            subEelective = request.form.get("elective")
            subInfo = (sub_class, sub_sem, sub_code, sub_abb, sub_name, subL, subT, subP, subEelective,CURR_BRANCH)
            subQuery = "INSERT INTO subjects( subclass, subsem, subcode, subabb, subname, sublecture, subtut, subprac, subelective,subdep) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            print(subQuery,"\n",subInfo)
            try:
                cursor.execute(subQuery, subInfo)
                conn.commit()
                return redirect("/add_subjects")
            except mysql.Error as error:
                return redirect(url_for("add_subject", error = error))
        else:
            error = request.args.get("error")
            if(error is None):
                error = ""
            cursor.execute("SELECT DISTINCT(class) FROM divisions WHERE department = %s", (CURR_BRANCH,))
            class_sub = cursor.fetchall()
            cursor.execute("SELECT * FROM subjects WHERE subdep =  %s",(CURR_BRANCH,))
            subjects = cursor.fetchall()
            return render_template("add_subjects.html",class_sub = class_sub, error = error,subjects = subjects)
    finally:
        conn.close()
    
@app.route("/remove_subject", methods = ["POST",])
@login_required
def remove_subject():
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        sub_rem = request.form.get("del_sub")
        del_sub_query = "DELETE FROM subjects WHERE subid = %s"
        del_sub_para = (sub_rem,)
        try:
            cursor.execute(del_sub_query,del_sub_para)
            conn.commit()
            return redirect("/add_subjects")
        except:
            error = "Subject is already Removed or Some other error has occured!"
            return redirect(url_for("add_subjects", error= error))
    finally:
        conn.close()



@app.route("/add_faculty", methods=["GET", "POST"])
@login_required
def add_faculty():
    CURR_BRANCH = session.get("username")
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        if request.method == "POST":
            facinit = request.form.get("faculty_initials")
            facname = request.form.get("faculty_name")
            facdes = request.form.get("faculty_designation")
            facqual = request.form.get("faculty_qualification")
            facshdep = request.form.get("shared_dep")
            facdep = CURR_BRANCH
            facInfo = ( facinit, facname, facdes, facqual, facdep,facshdep)
            facQuery = "INSERT INTO faculty( facinit, facname, facdes, facqual, facdep,facshdep) VALUES(%s,%s,%s,%s,%s,%s)"
            try:
                cursor.execute(facQuery, facInfo)
                conn.commit()
                return redirect("/add_faculty")
            except:
                error = "Faculty Already Exists or Input Given was Invalid!"
                return redirect(url_for("add_faculty", error = error))
                
        else:
            error = request.args.get("error")
            if(error is None):
                error = ""
            fac_query = f"SELECT * FROM faculty WHERE facdep LIKE %s OR facshdep LIKE %s"
            cursor.execute(fac_query,(f"%{CURR_BRANCH}%",f"%{CURR_BRANCH}%"))
            faculties = cursor.fetchall()
            print()
            return render_template("add_faculty.html", error = error,faculties = faculties)
    finally:
        conn.close()
    

@app.route("/remove_faculty", methods = ["POST",])
@login_required
def rem_fac():
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        del_fac = request.form.get("del_fac")
        del_fac_query = "DELETE FROM faculty WHERE facid = %s"
        del_fac_para = (del_fac,)
        try:
            cursor.execute(del_fac_query, del_fac_para)
            conn.commit()
            return redirect("/add_faculty")
        except:
            error = "Faculty Already Deleted or Some other error occured!"
            return redirect(url_for("add_faculty", error = error))
    finally:
        conn.close()




@app.route("/add_room", methods=["GET", "POST"])
@login_required
def add_room():
    CURR_BRANCH = session.get("username")
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        if request.method == "POST":
            roomno = request.form.get("room_no")
            roomdesc = request.form.get("room_desc")
            roomshdp = request.form.get("shared_dep")
            roomdep = CURR_BRANCH
            roomInfo = ( roomno, roomdesc, roomdep, roomshdp)
            roomQuery = "INSERT INTO rooms( roomno, roomdes, roomdep, roomshdep) VALUES(%s,%s,%s,%s)"
            try:
                cursor.execute( roomQuery, roomInfo)
                conn.commit()
                return redirect("/add_room")
            except:
                error = "Room Already Exists! Or Incorrect Data!"
                return redirect(url_for("add_room", error = error))
        else:
            error = request.args.get("error")
            if(error is None):
                error = ""
            room_query = f"SELECT * FROM rooms WHERE roomdep LIKE %s OR roomshdep LIKE %s"
            cursor.execute(room_query,(f"%{CURR_BRANCH}%",f"%{CURR_BRANCH}%"))
            rooms = cursor.fetchall()
            return render_template("add_room.html", error = error,rooms = rooms)
    finally:
        conn.close()
    
@app.route("/remove_room",methods=["POST",])
@login_required
def rem_room():
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        del_room = request.form.get("del_room")
        del_room_query = "DELETE FROM rooms WHERE roomid = %s"
        del_room_para = (del_room,)
        try:
            cursor.execute( del_room_query, del_room_para)
            conn.commit()
            return redirect("/add_room")
        except:
            error = "Room Already Deleted! Or Some other Problem arised!"
            return redirect(url_for("add_room", error = error))
    finally:
        conn.close()


@app.route("/add_div", methods=[ "GET", "POST"])
@login_required
def add_div():
    CURR_BRANCH = session.get("username")
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        if request.method == "POST":
            year = request.form.get("year")
            course = request.form.get("course")
            department = request.form.get("department")
            batch = request.form.get("batch")
            divisions = request.form.get("no_div")
            class_coll = year + " " + course+ " " + department
            div_para = (year, course, department, batch, divisions,class_coll)
            div_insert = "INSERT INTO divisions( year, course, department, batch, no_of_div,class) VALUES( %s, %s, %s, %s, %s,%s)"
            try:
                cursor.execute(div_insert, div_para)
                conn.commit()
                return redirect("/add_div")
            except:
                error = "Batch with No. of Divisions is already added!"
                return redirect(url_for("add_div", error = error))
        else:
            error = request.args.get("error")
            if(error is None):
                error = ""
            cursor.execute("SELECT * FROM divisions WHERE department = %s",(CURR_BRANCH,))
            div_table = cursor.fetchall()
            return render_template("add_div.html", error = error,div_table = div_table)
    finally:
        conn.close()


@app.route("/remove_div",methods=["POST",])
@login_required
def rem_div():
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        del_div = request.form.get("del_div")
        del_div_query = "DELETE FROM divisions WHERE id = %s"
        del_div_para = (del_div,)
        try:
            cursor.execute(del_div_query, del_div_para)
            conn.commit()
            return redirect("/add_div")
        except:
            error = "Batch already Deleted or Some other error occured!"
            return redirect(url_for("add_div", error = error))
    finally:
        conn.close()



@app.route("/get_div", methods = [ "GET", "POST"])
def get_div():
    CURR_YEAR_SEM = session.get("curr_year_sem")
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        if request.method == "POST":
            sel_class = request.get_json()
            sel_class = sel_class["sel_class"]
            sub_query = f"SELECT subabb FROM subjects WHERE subsem = %s AND subclass LIKE %s"
            div_query = f"SELECT batch,no_of_div FROM divisions WHERE class = %s"
            room_query = f"SELECT roomno FROM rooms"
            faculty_query = f"SELECT facinit FROM faculty"
            if(CURR_YEAR_SEM[0] == "O"):
                subsem = "ODD"
            else:
                subsem = "EVEN"
            sub_para = (subsem, f"%{sel_class}%")
            div_para = (sel_class,)
            cursor.execute(sub_query,sub_para)
            sub_res = cursor.fetchall()
            cursor.execute(div_query,div_para)
            div_res = cursor.fetchall()
            cursor.execute(room_query)
            room_res = cursor.fetchall()
            cursor.execute(faculty_query)
            faculty_res = cursor.fetchall()
            # This is to send back the data
            send_results = {
                "subjects" : sub_res,
                "divisions" : div_res,
                "rooms" : room_res,
                "faculty" : faculty_res
            }
            return jsonify(send_results)
    finally:
        conn.close()
    


@app.route("/get_room", methods = ["GET", "POST"])
def get_room():
    CURR_BRANCH = session.get("username")
    CURR_YEAR_SEM = session.get("curr_year_sem")
    if request.method == "POST":
        sel_room = request.get_json()
        sel_room = sel_room["getTableOf"]
        if(sel_room):
            complete_table = SELECT_room(sel_room,CURR_BRANCH,CURR_YEAR_SEM)
            send_results = {
                "complete_table": complete_table, 
            }
            return jsonify(send_results)
        
@app.route("/get_fac", methods = ["GET", "POST"])
def get_fac():
    CURR_BRANCH = session.get("username")
    CURR_YEAR_SEM = session.get("curr_year_sem")
    if request.method == "POST":
        sel_fac = request.get_json()
        sel_fac = sel_fac["getTableOf"]
        if(sel_fac):
            complete_table = SELECT_faculty(sel_fac,CURR_BRANCH,CURR_YEAR_SEM)
            send_results = {
                "complete_table": complete_table, 
            }
            return jsonify(send_results)
        

@app.route("/get_sub", methods = ["GET","POST"])
def get_sub():
    CURR_BRANCH = session.get("username")
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        if request.method == "POST":
            sel_sub = request.get_json()
            sel_sub = sel_sub["getSubject"]
            if(sel_sub):
                get_sub_query = "SELECT subelective FROM subjects WHERE subabb = %s AND subdep = %s"
                cursor.execute(get_sub_query,(sel_sub,CURR_BRANCH))
                get_sub_type = cursor.fetchall()
                if("E" in get_sub_type[0][0]):
                    get_sub_batch = [(sel_sub + "_"+ str(x + 1)) for x in range(20)]
                    send_results = {
                        "batchList": get_sub_batch
                    }
                    return jsonify(send_results),200
                else:
                    send_results = {
                        "batchList": "None"
                    }
                    return jsonify(send_results),200
    finally:
        conn.close()



# This is to remove particular slot from the timetable
@app.route("/remove_slot",methods=["POST",])
@login_required
def rem_slot():
    CURR_YEAR_SEM = session.get("curr_year_sem")
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        del_slot = request.form.get("del_slot")
        del_slot_query = f"DELETE FROM { CURR_YEAR_SEM } WHERE id = %s"
        del_slot_para = (del_slot,)
        try:
            cursor.execute(del_slot_query,del_slot_para)
            conn.commit()
            return redirect("/assign_slots")
        except:
            conn.rollback()
            error = "Slot is already deleted or Some other error occured!"
            return redirect(url_for("assign_slots", error = error))
    finally:
        conn.close()


@app.route("/assign_slots", methods=["GET","POST"])
@login_required
def assign_slots():
    CURR_BRANCH = session.get("username")
    CURR_YEAR_SEM = session.get("curr_year_sem")
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        if request.method == "POST":
            college_class_list = request.form.getlist("class")
            division_list = request.form.getlist("division")
            subject = request.form.get("subject")
            room = request.form.get("room")
            faculty = request.form.get("faculty")
            mult_faculty = request.form.get("multiple-faculty")
            batch = request.form.get("batch")
            slots = request.form.getlist("slots")
            type_submit = request.form.get("submit-button")

            pass_room_subjects = ["ED","WS-I","WS-II"]
            for college_class in college_class_list:
                for division in division_list:
                    cursor.execute("SELECT subelective FROM subjects WHERE subabb = %s AND subclass = %s", (subject,college_class))
                    subelective = cursor.fetchall()[0][0]
                    if(subelective.lower() == "yes"):
                        type_sub = "E".strip() + type_submit.strip()
                    else:
                        type_sub = type_submit

                    # Check for whether there is already a slot or not!
                    for slot in slots:
                        check_query_slot = f"SELECT batch,type FROM { CURR_YEAR_SEM } WHERE slot = %s AND class = %s AND division = %s"
                        cursor.execute(check_query_slot,(slot,college_class,division))
                        check_data_slot = cursor.fetchall()
                        if(len(check_data_slot) == 0):
                            continue
                        else:
                            if("E" in check_data_slot[0][1]):
                                continue
                            elif(check_data_slot[0][0] == "NO" and batch != "NO"):
                                errorin = "You cannot add batch when there is whole division already allotted for the slot!"
                                conn.rollback()
                                return redirect(url_for("assign_slots", error = errorin))
                            elif(check_data_slot[0][0] != "NO" and batch == "NO"):
                                errorin = "You cannot add Whole division when there a batch already allotted for the slot!"
                                conn.rollback()
                                return redirect(url_for("assign_slots", error = errorin))
                            

                    check_res = checkSubject(CURR_YEAR_SEM,CURR_BRANCH,subject,batch,type_sub,division,college_class)

                    if(check_res):
                        return redirect(url_for("assign_slots", error = check_res))

                    if("E" in type_sub):
                        fac_mult = ""
                        if(len(mult_faculty) > 0):
                            faculty = faculty.strip() + "/" + mult_faculty.strip()
                            fac_list = []
                            fac_index = 0
                            for j in range(len(faculty)):
                                if(faculty[j] == "/"):
                                    fac_list.append(faculty[fac_index:j])
                                    fac_index = j + 1
                            fac_list.append(faculty[fac_index:])
                            fac_mult = faculty
                            faculty = fac_list
                        if(len(fac_mult) != 0):
                            faculty = fac_mult
                        for slot in slots:
                            search_query = "SELECT day,time FROM time_slots WHERE slots_name = %s"
                            cursor.execute(search_query, (slot,))
                            time_slots = cursor.fetchall()[0]
                            insert_para = (college_class,subject,slot,time_slots[0],time_slots[1],faculty,room, batch, type_sub, CURR_BRANCH,division)
                            update_query = f"""INSERT INTO {CURR_YEAR_SEM}(class,subject,slot,day,time,faculty,room,batch,type,branch,division) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)"""
                            try:
                                cursor.execute(update_query,insert_para)
                            except mysql.Error as error:
                                conn.rollback()
                                return redirect(url_for("assign_slots", error = error))
                        continue
                            
                    check_query = f"SELECT * FROM { CURR_YEAR_SEM }  WHERE class = %s AND slot = %s AND batch = %s AND division = %s AND branch = %s"
                    if(len(slots) > 1):
                        for slot in slots:
                            check_para = (college_class,slot,batch,division, CURR_BRANCH)
                            cursor.execute( check_query, check_para)
                            check_res = cursor.fetchall()
                            if(len(check_res) > 0):
                                conn.rollback()
                                errorin = "Batch or Division has already been assigned slots"
                                return redirect(url_for("assign_slots", error = errorin))
                    else:
                        check_para = (college_class,slots[0],batch,division, CURR_BRANCH)
                        cursor.execute( check_query, check_para)
                        check_res = cursor.fetchall()
                        if(len(check_res) > 0):
                            conn.rollback()
                            errorin = "Batch or Division has already been assigned slots"
                            return redirect(url_for("assign_slots", error = errorin))
                        
                    if(len(mult_faculty) > 0):
                        faculty = faculty.strip() + "/" + mult_faculty.strip()
                        fac_list = []
                        fac_index = 0
                        for j in range(len(faculty)):
                            if(faculty[j] == "/"):
                                fac_list.append(faculty[fac_index:j])
                                fac_index = j + 1
                        fac_list.append(faculty[fac_index:])
                        for curr_fac in fac_list:
                            for slot in slots:
                                room_query = f"SELECT * FROM {CURR_YEAR_SEM} WHERE room = %s AND slot = %s"
                                room_para = (room,slot)
                                cursor.execute(room_query,room_para)
                                room_res = cursor.fetchall()
                                batch_query = f"SELECT * FROM {CURR_YEAR_SEM} WHERE slot = %s AND batch = %s AND division = %s AND class = %s"
                                batch_para = (slot,batch,division,college_class)
                                cursor.execute(batch_query, batch_para)
                                batch_res = cursor.fetchall()
                                if(len(room_res) >= 1 and subject not in pass_room_subjects):
                                    conn.rollback()
                                    errorin = "Room is already alloted for that slot!"
                                    return redirect(url_for("assign_slots", error = errorin))
                                elif(len(batch_res) >= 1):
                                    conn.rollback()
                                    errorin = "Batch of that Division is already alloted for that slot!"
                                    return redirect(url_for("assign_slots", error = errorin))
                                fac_query = f"SELECT * FROM {CURR_YEAR_SEM} WHERE slot = %s AND (faculty  LIKE  %s)"
                                fac_para = (slots[0],f"%{curr_fac}%")
                                cursor.execute(fac_query,fac_para)
                                fac_res = cursor.fetchall()
                                if(len(fac_res) >= 1):
                                    conn.rollback()
                                    errorin = "Faculty is already alloted for that slot!"
                                    return redirect(url_for("assign_slots", error = errorin))
                        for slot in slots:
                            search_query = "SELECT day,time FROM time_slots WHERE slots_name = %s"
                            cursor.execute(search_query, (slot,))
                            time_slots = cursor.fetchall()[0]
                            insert_para = (college_class,subject,slot,time_slots[0],time_slots[1],faculty,room, batch, type_sub, CURR_BRANCH,division)
                            insert_query = f"""INSERT INTO {CURR_YEAR_SEM}(class,subject,slot,day,time,faculty,room,batch,type,branch,division) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)"""
                            try:
                                cursor.execute(insert_query,insert_para)
                            except mysql.Error as error:
                                conn.rollback()
                                return redirect(url_for("assign_slots", error = error))
                        continue      
                    else:
                        for slot in slots:
                            room_query = f"SELECT * FROM {CURR_YEAR_SEM} WHERE room = %s AND slot = %s"
                            room_para = (room,slot)
                            cursor.execute(room_query,room_para)
                            room_res = cursor.fetchall()
                            batch_query = f"SELECT * FROM {CURR_YEAR_SEM} WHERE slot = %s AND batch = %s AND division = %s AND class = %s"
                            batch_para = (slot,batch,division,college_class)
                            cursor.execute(batch_query, batch_para)
                            batch_res = cursor.fetchall()
                            if(len(room_res) >= 1  and subject not in pass_room_subjects):
                                conn.rollback()
                                errorin = "Room is already alloted for that slot!"
                                return redirect(url_for("assign_slots", error = errorin))
                            elif(len(batch_res) >= 1):
                                conn.rollback()
                                errorin = "Batch of that Division is already alloted for that slot!"
                                return redirect(url_for("assign_slots", error = errorin))
                        for slot in slots:
                            search_query = "SELECT day,time FROM time_slots WHERE slots_name = %s"
                            cursor.execute(search_query, (slot,))
                            time_slots = cursor.fetchall()[0]
                            insert_para = (college_class,subject,slot,time_slots[0],time_slots[1],faculty,room, batch, type_sub, CURR_BRANCH,division)
                            insert_query = f"""INSERT INTO {CURR_YEAR_SEM}(class,subject,slot,day,time,faculty,room,batch,type,branch,division) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)"""
                            try:
                                cursor.execute(insert_query,insert_para)
                            except mysql.Error as error:
                                conn.rollback()
                                return redirect(url_for("assign_slots", error = error))
                        continue
            conn.commit()
            error = "Successfully Inserted Slot!"
            return redirect(url_for("assign_slots", error = error)) 
        else:
            error = request.args.get("error")
            if(error is None):
                error = ""
            input_class_query = "SELECT DISTINCT(class) FROM divisions WHERE department = %s"
            input_class_para = ( CURR_BRANCH, )
            slots_para = "SELECT slots_name,slot_time_day FROM time_slots ORDER BY id ASC"
            cursor.execute(slots_para)
            slots_res = cursor.fetchall()
            cursor.execute(input_class_query, input_class_para)
            input_class_res = cursor.fetchall()
            query = f"SELECT id,class,subject,slot,day,time,faculty,room,division,batch,type FROM { CURR_YEAR_SEM } WHERE branch = %s ORDER BY ID DESC"
            cursor.execute(query,(CURR_BRANCH,))
            results = cursor.fetchall()
            return render_template("assign.html", CURR_YEAR_SEM = CURR_YEAR_SEM, results = results,slots_res = slots_res, input_class_res = input_class_res,error = error)
    finally:
        conn.close()    


@app.route("/show_timetable", methods=["GET","POST"])
@login_required
def show_timetable():
    CURR_BRANCH = session.get("username")
    CURR_YEAR_SEM = session.get("curr_year_sem")
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        if request.method == "POST":
            request_type = request.form.get("button_submit")
            sel_class = request.form.get("sel_class")
            if(request_type == "edit" and sel_class):
                return redirect(url_for("view_edit",sel_class = sel_class))
            if(request_type == "swap" and sel_class):
                return redirect(url_for("view_swap",sel_class = sel_class))
            sel_room = request.form.get("sel_room")
            sel_fac = request.form.get("sel_fac")
            if(sel_class):
                show_class = f"Class: {sel_class}"
                complete_table = SELECT_class(sel_class,CURR_BRANCH,CURR_YEAR_SEM)
                class_query = "SELECT DISTINCT(class),batch FROM divisions WHERE department = %s"
                room_query = "SELECT roomno FROM rooms"
                fac_query = "SELECT facinit FROM faculty"
                class_para = (CURR_BRANCH,)
                cursor.execute(class_query, class_para)
                class_res = cursor.fetchall()
                cursor.execute(room_query)
                room_res = cursor.fetchall()
                cursor.execute(fac_query)
                fac_res = cursor.fetchall()
                return render_template("show_timetable.html", CURR_YEAR_SEM = CURR_YEAR_SEM, class_res = class_res, room_res = room_res, fac_res = fac_res,infoImpo = show_class,timetable = complete_table)
            elif(sel_room):
                show_room = f"Room: {sel_room}"
                complete_table = SELECT_room(sel_room,CURR_BRANCH,CURR_YEAR_SEM)
                class_query = "SELECT DISTINCT(class),batch FROM divisions WHERE department = %s"
                room_query = "SELECT roomno FROM rooms"
                fac_query = "SELECT facinit FROM faculty"
                class_para = (CURR_BRANCH,)
                cursor.execute(class_query, class_para)
                class_res = cursor.fetchall()
                cursor.execute(room_query)
                room_res = cursor.fetchall()
                cursor.execute(fac_query)
                fac_res = cursor.fetchall()
                return render_template("show_timetable.html", CURR_YEAR_SEM = CURR_YEAR_SEM, class_res = class_res, room_res = room_res, fac_res = fac_res,infoImpo = show_room,timetable = complete_table)
            elif(sel_fac):
                show_faculty = ""
                fac_load = ""
                complete_table = SELECT_faculty(sel_fac,CURR_BRANCH,CURR_YEAR_SEM)
                class_query = "SELECT DISTINCT(class),batch FROM divisions WHERE department = %s"
                room_query = "SELECT roomno FROM rooms"
                fac_query = "SELECT facinit FROM faculty"
                class_para = (CURR_BRANCH,)
                cursor.execute(class_query, class_para)
                class_res = cursor.fetchall()
                cursor.execute(room_query)
                room_res = cursor.fetchall()
                cursor.execute(fac_query)
                fac_res = cursor.fetchall()
                show_fac_query = "SELECT facname FROM faculty WHERE facinit = %s"
                show_fac_para = (sel_fac,)
                cursor.execute(show_fac_query, show_fac_para)
                show_fac_res = cursor.fetchall()
                show_faculty = f"Faculty: {show_fac_res[0][0]} ({sel_fac})"
                lec_load_query = f"""SELECT 
                                    COUNT(*) as count
                                FROM (
                                    SELECT
                                        subject, 
                                        slot, 
                                        day, 
                                        time, 
                                        faculty, 
                                        room,  
                                        type
                                    FROM 
                                        {CURR_YEAR_SEM}
                                    WHERE faculty LIKE %s and type LIKE "%L%"
                                    GROUP BY
                                        subject, 
                                        slot, 
                                        day, 
                                        time, 
                                        faculty, 
                                        room, 
                                        type
                                ) as unique_rows;"""
                prac_load_query = f"""SELECT 
                                    COUNT(*) as count
                                FROM (
                                    SELECT
                                        subject, 
                                        slot, 
                                        day, 
                                        time, 
                                        faculty, 
                                        room, 
                                        type
                                    FROM 
                                        {CURR_YEAR_SEM}
                                    WHERE faculty LIKE %s and type LIKE "%P%"
                                    GROUP BY
                                        subject, 
                                        slot, 
                                        day, 
                                        time, 
                                        faculty, 
                                        room,
                                        type
                                ) as unique_rows;"""
                tut_load_query = f"""SELECT 
                                    COUNT(*) as count
                                FROM (
                                    SELECT 
                                        subject, 
                                        slot, 
                                        day, 
                                        time, 
                                        faculty, 
                                        room,
                                        type
                                    FROM 
                                        {CURR_YEAR_SEM}
                                    WHERE faculty LIKE %s and type LIKE "%T%"
                                    GROUP BY 
                                        subject, 
                                        slot, 
                                        day, 
                                        time, 
                                        faculty, 
                                        room, 
                                        type
                                ) as unique_rows;"""
                cursor.execute(lec_load_query,(f"%{sel_fac}%",))
                lec_load = cursor.fetchall()[0][0]
                cursor.execute(prac_load_query,(f"%{sel_fac}%",))
                prac_load = cursor.fetchall()[0][0]
                cursor.execute(tut_load_query,(f"%{sel_fac}%",))
                tut_load = cursor.fetchall()[0][0]
                total_load = lec_load + tut_load + prac_load
                fac_load = f"Theory: {lec_load} Tutorial: {tut_load} Practical: {prac_load} Total Load: {total_load}"
                return render_template("show_timetable.html", CURR_YEAR_SEM = CURR_YEAR_SEM, class_res = class_res, room_res = room_res, fac_res = fac_res,infoImpo = show_faculty,fac_load = fac_load,timetable = complete_table)
            class_query = "SELECT DISTINCT(class),batch FROM divisions WHERE department = %s"
            room_query = "SELECT roomno FROM rooms"
            fac_query = "SELECT facinit FROM faculty"
            class_para = (CURR_BRANCH,)
            cursor.execute(class_query, class_para)
            class_res = cursor.fetchall()
            cursor.execute(room_query)
            room_res = cursor.fetchall()
            cursor.execute(fac_query)
            fac_res = cursor.fetchall()
            return render_template("show_timetable.html", CURR_YEAR_SEM = CURR_YEAR_SEM, class_res = class_res, room_res = room_res, fac_res = fac_res)
        else:
            class_query = "SELECT DISTINCT(class),batch FROM divisions WHERE department = %s"
            room_query = "SELECT roomno FROM rooms"
            fac_query = "SELECT facinit FROM faculty"
            class_para = (CURR_BRANCH,)
            cursor.execute(class_query, class_para)
            class_res = cursor.fetchall()
            cursor.execute(room_query)
            room_res = cursor.fetchall()
            cursor.execute(fac_query)
            fac_res = cursor.fetchall()
            return render_template("show_timetable.html", CURR_YEAR_SEM = CURR_YEAR_SEM, class_res = class_res, room_res = room_res, fac_res = fac_res)
    finally:
        conn.close()
    


@app.route("/edit_slots", methods = ["GET","POST"])
@login_required
def edit_slots():
    CURR_BRANCH = session.get("username")
    CURR_YEAR_SEM = session.get("curr_year_sem")
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        if request.method == "POST":
            slots_to_edit = request.form.get("slots_edit")
            if(slots_to_edit == "()"):
                return redirect("/assign_slots")
            slots_id = ast.literal_eval(slots_to_edit)
            if(len(slots_id) > 2):
                error = "Only 2 slots can be edited at a time!"
                return redirect(url_for("assign_slots",error = error))
            slots_info = []
            slot_query = f"SELECT * FROM { CURR_YEAR_SEM } WHERE id = %s"
            for slot_id in slots_id:
                cursor.execute( slot_query, (slot_id,))
                info_res = cursor.fetchall()[0]
                slots_info.append(info_res)
            input_class_query = "SELECT DISTINCT(class) FROM divisions WHERE department = %s"
            input_class_para = ( CURR_BRANCH, )
            slots_para = "SELECT slots_name,slot_time_day FROM time_slots ORDER BY id ASC"
            cursor.execute(slots_para)
            slots_res = cursor.fetchall()
            cursor.execute(input_class_query, input_class_para)
            input_class_res = cursor.fetchall()
            query = f"SELECT id,class,subject,slot,day,time,faculty,room,division,batch,type FROM { CURR_YEAR_SEM } ORDER BY ID DESC"
            cursor.execute(query)
            results = cursor.fetchall()
            return render_template("edit_slots.html", CURR_YEAR_SEM = CURR_YEAR_SEM, results = results,slots_res = slots_res, input_class_res = input_class_res,slots = slots_info)
        else:
            error = request.args.get("error")
            slots_to_edit = request.args.getlist("slots_edit")
            if(slots_to_edit == "()"):
                return redirect("/assign_slots")
            slots_id = slots_to_edit
            slots_info = []
            slot_query = f"SELECT * FROM { CURR_YEAR_SEM } WHERE id = %s"
            for slot_id in slots_id:
                cursor.execute( slot_query, (slot_id,))
                info_res = cursor.fetchall()
                info_res = info_res[0]
                slots_info.append(info_res)
            input_class_query = "SELECT DISTINCT(class) FROM divisions WHERE department = %s"
            input_class_para = ( CURR_BRANCH, )
            slots_para = "SELECT slots_name,slot_time_day FROM time_slots ORDER BY id ASC"
            cursor.execute(slots_para)
            slots_res = cursor.fetchall()
            cursor.execute(input_class_query, input_class_para)
            input_class_res = cursor.fetchall()
            query = f"SELECT id,class,subject,slot,day,time,faculty,room,division,batch,type FROM { CURR_YEAR_SEM } ORDER BY ID DESC"
            cursor.execute(query)
            results = cursor.fetchall()
            return render_template("edit_slots.html", CURR_YEAR_SEM = CURR_YEAR_SEM, results = results,slots_res = slots_res, input_class_res = input_class_res,slots = slots_info,error = error)
    finally:
        conn.close()

@app.route("/change_slots", methods = ["POST",])
@login_required
def change_slots():
    CURR_BRANCH = session.get("username")
    CURR_YEAR_SEM = session.get("curr_year_sem")
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM temp_data")
        conn.commit()
        error = ""
        slot_id = request.form.getlist("slot_id_curr")
        copy_data = f"INSERT INTO temp_data (SELECT * FROM {CURR_YEAR_SEM} WHERE id = %s)"
        for slot_part in slot_id:
            cursor.execute(copy_data,(slot_part,))
        for curr_row in range(len(slot_id)):
            check_update_double = {}
            slots_changed = {}
            curr_slot_id = slot_id[curr_row]
            slot_class = request.form.getlist("class")[curr_row] or request.form.getlist("class_bef")[curr_row]
            slot_div = request.form.getlist("division")[curr_row] or request.form.getlist("division_bef")[curr_row]
            slot_batch = request.form.getlist("batch")[curr_row] or request.form.getlist("batch_bef")[curr_row]
            slot_sub = request.form.getlist("subject_bef")[curr_row]
            slot_fac = request.form.getlist("faculty")[curr_row] or request.form.getlist("faculty_bef")[curr_row]
            slot_room = request.form.getlist("room")[curr_row] or request.form.getlist("room_bef")[curr_row]
            slot_slot = request.form.getlist("slot")[curr_row] or request.form.getlist("slots_bef")[curr_row]
            print(request.form.getlist("sub_type"))
            print(request.form.get("sub_type"))
            slot_type = request.form.getlist("sub_type")[curr_row]



            slot_sub_type = request.form.getlist("sub_type")[curr_row]
            get_time_slot = "SELECT day,time FROM time_slots WHERE slots_name = %s"
            cursor.execute( get_time_slot, ( slot_slot,))
            time_res = cursor.fetchall()[0]

            
            change_class= False
            change_div = False
            change_batch = False
            change_slot = False
            change_fac = False
            change_room = False
            
            if(request.form.getlist("class")[curr_row] != request.form.getlist("class_bef")[curr_row] and (request.form.getlist("class")[curr_row] != "")):
                change_class = True

            if(request.form.getlist("division")[curr_row] != request.form.getlist("division_bef")[curr_row] and (request.form.getlist("division")[curr_row] != "")):
                change_div = True

            if((request.form.getlist("batch")[curr_row] != request.form.getlist("batch_bef")[curr_row])and (request.form.getlist("batch")[curr_row] != "")):
                change_batch = True

            if( (request.form.getlist("faculty")[curr_row] != request.form.getlist("faculty_bef")[curr_row]) and (request.form.getlist("faculty")[curr_row] != "")):
                change_fac = True

            if((request.form.getlist("room")[curr_row] != request.form.getlist("room_bef")[curr_row] ) and (request.form.getlist("room")[curr_row] != "")):
                change_room = True

            if((request.form.getlist("slot")[curr_row] != request.form.getlist("slot")[curr_row] ) and (request.form.getlist("slot")[curr_row] != "")):
                change_slot
                    
            if(change_batch and ("E" in slot_type)):
                if(slot_batch != "NO"):
                    error = "Subject is elective so batches are not allowed!"
                    return redirect(url_for("edit_slots",error = error,slots_edit = slot_id))
                    


            if((not change_class) and (not change_div) and (not change_batch) and (not change_fac) and (not change_room) and (change_slot)):
                all_para = ( slot_class, slot_sub, slot_slot, slot_fac, slot_room, slot_batch, CURR_BRANCH, slot_div)
                all_res = check_data( CURR_YEAR_SEM, all_para=all_para)
                if(all_res):
                    error = "Slot cannot be changed as it already has been assigned for some other slot!"
                    return redirect(url_for("edit_slots",error = error,slots_edit = slot_id))
                else:
                    update_slot_query = f"UPDATE { CURR_YEAR_SEM } SET class = %s, division = %s ,batch = %s, subject = %s, faculty = %s, room = %s, slot = %s, day = %s, time = %s, type = %s WHERE id = %s"
                    update_slot_para = ( slot_class, slot_div, slot_batch, slot_sub, slot_fac, slot_room, slot_slot,time_res[0],time_res[1],slot_sub_type, curr_slot_id)
                    try:
                        cursor.execute(update_slot_query, update_slot_para)
                    except mysql.Error as error:
                        conn.rollback()
                        return redirect(url_for("edit_slots",error = error,slots_edit = slot_id))
                
            

            if(len(slot_id) > 1):
                for check_slot in range(len(slot_id)):
                    change_room_fac_don = False
                    if(curr_row == check_slot):
                        continue
                    check_curr_slot_id = slot_id[check_slot]

                    if(change_div or change_batch):
                        div_para = ( slot_class, slot_slot, slot_batch, slot_div, CURR_BRANCH)
                        div_res = check_data(CURR_YEAR_SEM, div_para= div_para)
                        if(div_res):
                            conn.rollback()
                            error = error + f"Division or Batch {slot_batch} had already been  allotted \n"
                            return redirect(url_for("edit_slots", error = error, slots_edit = slot_id))

                    if(change_fac and change_room):
                        check_slot_query = f"SELECT * FROM temp_data WHERE id = %s AND faculty = %s OR room = %s"
                        check_slot_para = ( check_curr_slot_id, slot_fac, slot_room)
                        cursor.execute(check_slot_query, check_slot_para)
                        check_slot_res = cursor.fetchall()
                        if(len(check_slot_res) >= 1):
                            if(check_curr_slot_id in check_update_double):
                                conn.rollback()
                                error = f"In edit two or more ids this ({check_update_double}) tried to have same value for id {check_curr_slot_id}"
                                return redirect(url_for("edit_slots",error = error,slots_edit = slot_id))
                            update_slot_query = f"UPDATE { CURR_YEAR_SEM } SET faculty = %s,room = %s WHERE id = %s"
                            update_slot_para = (slot_fac,slot_room,curr_slot_id)
                            try:
                                cursor.execute(update_slot_query, update_slot_para)
                            except mysql.Error as error:
                                conn.rollback()
                                return redirect(url_for("edit_slots",error = error,slots_edit = slot_id))
                            check_update_double[check_curr_slot_id] = curr_slot_id
                            slots_changed[curr_slot_id] = 1
                            change_room_fac_don =  True

                    if(change_fac and not change_room_fac_don):
                
                        check_slot_query = f"SELECT * FROM temp_data WHERE id = %s AND faculty = %s"
                        check_slot_para = ( check_curr_slot_id, slot_fac)
                        cursor.execute(check_slot_query, check_slot_para)
                        check_slot_res = cursor.fetchall()
                        if(len(check_slot_res) == 1):
                            if(check_curr_slot_id in check_update_double):
                                conn.rollback()
                                error = f"In edit two or more ids this ({check_update_double}) tried to have same value for id {check_curr_slot_id}"
                                return redirect(url_for("edit_slots",error = error,slots_edit = slot_id))
                            update_slot_query = f"UPDATE { CURR_YEAR_SEM } SET faculty = %s WHERE id = %s"
                            update_slot_para = (slot_fac,curr_slot_id)
                            try:
                                cursor.execute(update_slot_query, update_slot_para)
                            except mysql.Error as error:
                                conn.rollback()
                                return redirect(url_for("edit_slots",error = error,slots_edit = slot_id))
                            check_update_double[check_curr_slot_id] = curr_slot_id
                            slots_changed[curr_slot_id] = 1
                        else:
                            fac_para = ( slot_slot, f"%{slot_fac}%")
                            fac_res = check_data(CURR_YEAR_SEM,fac_para= fac_para)
                            if(fac_res):
                                error = error + f"Faculty {slot_fac} had already been allotted \n"
                                return redirect(url_for("edit_slots",error = error,slots_edit = slot_id))


                    if(change_room and not change_room_fac_don):

                        check_slot_query = f"SELECT * FROM temp_data WHERE id = %s AND room = %s"
                        check_slot_para = ( check_curr_slot_id, slot_room)
                        cursor.execute(check_slot_query, check_slot_para)
                        check_slot_res = cursor.fetchall()
                        if(len(check_slot_res) == 1):
                            if(check_curr_slot_id in check_update_double):
                                conn.rollback()
                                error = f"In edit two or more ids this ({check_update_double}) tried to have same value for id {check_curr_slot_id}"
                                return redirect(url_for("edit_slots",error = error,slots_edit = slot_id))
                            update_slot_query = f"UPDATE { CURR_YEAR_SEM } SET room = %s WHERE id = %s"
                            update_slot_para = (slot_room,curr_slot_id)
                            print("Room update Slot : ",update_slot_para)
                            try:
                                print("Succesfull update",update_slot_para)
                                cursor.execute(update_slot_query, update_slot_para)
                            except mysql.Error as error:
                                conn.rollback()
                                return redirect(url_for("edit_slots",error = error,slots_edit = slot_id))
                            check_update_double[check_curr_slot_id] = curr_slot_id
                            slots_changed[curr_slot_id] = 1
                        else:
                            room_para = (slot_slot, slot_room)
                            room_res = check_data( CURR_YEAR_SEM, room_para= room_para)
                            if(room_res):
                                error = error + f"Room {slot_room} had already been allotted \n"
                                return redirect(url_for("edit_slots",error = error,slots_edit = slot_id))

                    check_slot_para = ( check_curr_slot_id, slot_class, slot_div, slot_batch, slot_sub, slot_fac, slot_room, slot_slot,slot_sub_type, CURR_BRANCH)
                    check_slot_query = f"SELECT * FROM temp_data WHERE id = %s AND class = %s AND division = %s AND batch = %s AND subject = %s AND faculty = %s AND room = %s AND slot = %s AND type = %s AND branch = %s"
                    cursor.execute(check_slot_query, check_slot_para)
                    check_slot_res = cursor.fetchall()
                    if(len(check_slot_res) >= 1):
                        if(check_curr_slot_id in check_update_double):
                            conn.rollback()
                            error = f"In edit two or more ids this ({check_update_double}) tried to have same value for id {check_curr_slot_id}"
                            return redirect(url_for("edit_slots",error = error,slots_edit = slot_id))
                        update_slot_query = f"UPDATE { CURR_YEAR_SEM } SET class = %s, division = %s ,batch = %s, subject = %s, faculty = %s, room = %s, slot = %s, day = %s, time = %s, type = %s WHERE id = %s"
                        update_slot_para = ( slot_class, slot_div, slot_batch, slot_sub, slot_fac, slot_room, slot_slot,time_res[0],time_res[1],slot_sub_type, curr_slot_id)
                        try:
                            cursor.execute(update_slot_query, update_slot_para)
                        except mysql.Error as error:
                            conn.rollback()
                            return redirect(url_for("edit_slots",error = error,slots_edit = slot_id))
                        check_update_double[check_curr_slot_id] = curr_slot_id
                        slots_changed[curr_slot_id] = 1

                if(curr_slot_id in slots_changed):
                    continue
                else:
                    div_para = ( slot_class, slot_slot, slot_batch, slot_div, CURR_BRANCH)
                    all_para = ( slot_class, slot_sub, slot_slot, slot_fac, slot_room, slot_batch, CURR_BRANCH, slot_div)
                    fac_para = ( slot_slot, f"%{slot_fac}%")
                    room_para = ( slot_slot, slot_room)
                    div_res = False
                    fac_res = False
                    room_res = False
                    all_res = False
                    if(((request.form.getlist("division")[curr_row] != request.form.getlist("division_bef")[curr_row]) and (request.form.getlist("division")[curr_row] != ""))):
                        div_res = check_data( CURR_YEAR_SEM, div_para=div_para)
                    if( (request.form.getlist("faculty")[curr_row] != request.form.getlist("faculty_bef")[curr_row]) and (request.form.getlist("faculty")[curr_row] != "")):
                        fac_res = check_data( CURR_YEAR_SEM, fac_para=fac_para)
                    if((request.form.getlist("room")[curr_row] != request.form.getlist("room_bef")[curr_row] ) and (request.form.getlist("room")[curr_row] != "")):
                        print("ROoom Resoultuin     ")
                        room_res = check_data( CURR_YEAR_SEM, room_para=room_para)
                        print(room_res)
                    if(div_res and room_res and fac_res):
                        all_res = check_data( CURR_YEAR_SEM, all_para=all_para)
                    if(div_res or all_res or fac_res or room_res):
                        conn.rollback()
                        if(all_res):
                            error = error + f"Duplicate Entry\n"
                        if(div_res):
                            error = error + f"Division or Batch {slot_batch} had already been  allotted \n"
                        if(fac_res):
                            error = error + f"Faculty {slot_fac} had already been allotted \n"
                        if(room_res):
                            error = error + f"Room {slot_room} had already been allotted \n"
                        return redirect(url_for("edit_slots",error = error,slots_edit = slot_id))
                    else:
                        update_slot_query = f"UPDATE { CURR_YEAR_SEM } SET class = %s, division = %s ,batch = %s, subject = %s, faculty = %s, room = %s, slot = %s, day = %s, time = %s, type = %s WHERE id = %s"
                        update_slot_para = ( slot_class, slot_div, slot_batch, slot_sub, slot_fac, slot_room, slot_slot,time_res[0],time_res[1],slot_sub_type, curr_slot_id)
                        try:
                            cursor.execute(update_slot_query, update_slot_para)
                        except mysql.Error as error:
                            conn.rollback()
                            return redirect(url_for("edit_slots",error = error,slots_edit = slot_id))
            elif(len(slot_id) == 1):
                div_para = ( slot_class, slot_slot, slot_batch, slot_div, CURR_BRANCH)
                all_para = ( slot_class, slot_sub, slot_slot, slot_fac, slot_room, slot_batch, CURR_BRANCH, slot_div)
                fac_para = ( slot_slot, f"%{slot_fac}%")
                room_para = ( slot_slot, slot_room)
                div_res = False
                fac_res = False
                room_res = False
                all_res = False
                if(((request.form.getlist("division")[curr_row] != request.form.getlist("division_bef")[curr_row]) and (request.form.getlist("division")[curr_row] != ""))):
                    div_res = check_data( CURR_YEAR_SEM, div_para=div_para)
                if( (request.form.getlist("faculty")[curr_row] != request.form.getlist("faculty_bef")[curr_row]) and (request.form.getlist("faculty")[curr_row] != "")):
                    fac_res = check_data( CURR_YEAR_SEM, fac_para=fac_para)
                if((request.form.getlist("room")[curr_row] != request.form.getlist("room_bef")[curr_row] ) and (request.form.getlist("room")[curr_row] != "")):
                    room_res = check_data( CURR_YEAR_SEM, room_para=room_para)
                if(div_res and room_res and fac_res):
                    all_res = check_data( CURR_YEAR_SEM, all_para=all_para)
                if(div_res or all_res or fac_res or room_res):
                    conn.rollback()
                    if(all_res):
                        error = error + f"Duplicate Entry \n"
                    if(div_res):
                        error = error + f"Division or Batch {slot_batch} had already been  allotted \n"
                    if(fac_res):
                        error = error + f"Faculty {slot_fac} had already been allotted \n"
                    if(room_res):
                        error = error + f"Room {slot_room} had already been allotted \n"
                    return redirect(url_for("edit_slots",error = error,slots_edit = slot_id))
                else:
                    print("Direct to update")
                    update_slot_query = f"UPDATE { CURR_YEAR_SEM } SET class = %s, division = %s ,batch = %s, subject = %s, faculty = %s, room = %s, slot = %s, day = %s, time = %s, type = %s WHERE id = %s"
                    update_slot_para = ( slot_class, slot_div, slot_batch, slot_sub, slot_fac, slot_room, slot_slot,time_res[0],time_res[1],slot_sub_type, curr_slot_id)
                    try:
                        cursor.execute(update_slot_query, update_slot_para)
                    except mysql.Error as error:
                        conn.rollback()
                        return redirect(url_for("edit_slots",error = error,slots_edit = slot_id))
                
            else:
                error = "Some other unencountered error occured! Please go back to home page"
                return redirect(url_for("edit_slots",error = error,slots_edit = slot_id))
            conn.commit()
        return redirect(url_for("assign_slots",error = "Successfully Changed the data!"))
    finally:
        conn.close()






@app.route("/view_edit", methods = ["GET","POST"])
@login_required
def view_edit():
    CURR_BRANCH = session.get("username")
    CURR_YEAR_SEM = session.get("curr_year_sem")
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        if request.method == "POST":
            return redirect("/show_timetable")
        else:      
            sel_class = request.args.get("sel_class")
            infoImpo = f"Class: {sel_class}"
            division_sep = sel_class.split(" ")[-1]
            comm_class = " ".join(sel_class.split(" ")[0:-1])
            if(CURR_YEAR_SEM[0] == "O"):
                subsem = "ODD"
            else:
                subsem = "EVEN"
            view_query = f"SELECT no_of_div,class FROM divisions WHERE batch = %s AND department = %s"
            view_para = (division_sep,CURR_BRANCH)
            cursor.execute(view_query,view_para)
            view_res = cursor.fetchall()[0]
            if(len(division_sep) >= 2):
                add_symbol = "-"
            else:
                add_symbol = ""
            all_batch = [(division_sep+ add_symbol +str(x+1)) for x in range(view_res[0])]
            cursor.execute("SELECT roomno FROM rooms")
            room_res = cursor.fetchall()
            cursor.execute("SELECT facinit FROM faculty")
            fac_res = cursor.fetchall()
            cursor.execute("SELECT subabb FROM subjects WHERE subclass = %s AND subsem = %s",(comm_class,subsem))
            sub_res = cursor.fetchall()
            complete_table = SELECT_class(sel_class,CURR_BRANCH,CURR_YEAR_SEM)
            return render_template("view_edit_nav.html",timetable = complete_table,CURR_YEAR_SEM = CURR_YEAR_SEM,infoImpo = infoImpo,
            sel_class = sel_class,all_batch = all_batch,room_res = room_res,fac_res =fac_res,sub_res =sub_res,div_class = view_res[1])
    finally:
        conn.close()
    


@app.route("/view_edit_check_api", methods = ["POST",])
def view_edit_check_api():
    CURR_BRANCH = session.get("username")
    CURR_YEAR_SEM = session.get("curr_year_sem")
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        if request.method == "POST":
            error = ""
            slot_info = request.get_json()
            slot_class = slot_info["class"]
            slot_div = slot_info["division"]
            slot_sub = slot_info["subject"]
            slot_room = slot_info["room"]
            slot_fac = slot_info["faculty"]
            slot_batch = slot_info["batch"]
            slot_slot = slot_info["slot"]
            slot_type = slot_info["type"]


            pass_room_subjecs = ["ED","WS-I","WS-II"]


            cursor.execute("SELECT subelective FROM subjects WHERE subabb = %s AND subclass = %s", (slot_sub,slot_class))
            subelective = cursor.fetchall()[0][0]
            if(subelective.lower() == "yes"):
                type_sub = "E".strip() + slot_type.strip()
            else:
                type_sub = slot_type

            check_query_slot = f"SELECT batch,type FROM { CURR_YEAR_SEM } WHERE slot = %s AND class = %s AND division = %s"
            cursor.execute(check_query_slot,(slot_slot,slot_class,slot_div))
            check_data_slot = cursor.fetchall()
            if(len(check_data_slot) == 0):
                pass
            else:
                if("E" in check_data_slot[0][1]):
                    pass
                elif(check_data_slot[0][0] == "NO" and slot_batch != "NO"):
                    errorin = "You cannot add batch when there is whole division already allotted for the slot!"
                    return(jsonify({"error": errorin}),400)
                elif(check_data_slot[0][0] != "NO" and slot_batch == "NO"):
                    errorin = "You cannot add Whole division when there a batch already allotted for the slot!"
                    return(jsonify({"error": errorin}),400)
            
            check_res = checkSubject(CURR_YEAR_SEM,CURR_BRANCH,slot_sub,slot_batch,type_sub,slot_div,slot_class)

            if(check_res):
                return(jsonify({"error": check_res}),400)
            
            if("E" in type_sub):
                time_query = "SELECT day,time FROM time_slots WHERE slots_name = %s"
                cursor.execute(time_query,(slot_slot,))
                time_res = cursor.fetchall()[0]
                update_query = f"INSERT INTO { CURR_YEAR_SEM }(class,subject,slot,day,time,faculty,room,batch,type,branch,division) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                update_para = (slot_class,slot_sub,slot_slot,time_res[0],time_res[1],slot_fac,slot_room,slot_batch,type_sub,CURR_BRANCH,slot_div)
                try:
                    cursor.execute(update_query,update_para)
                    conn.commit()
                    error = f"Successfully Inserted the value inTable { CURR_YEAR_SEM }"
                    return(jsonify({"error": error}),200)
                except mysql.Error as error:
                    conn.rollback()
                    return(jsonify({"error": str(error)}),400)

            # To check for all the clashes
            # All parameters first
            fac_para = ( slot_slot, f"%{slot_fac}%")
            room_para = ( slot_slot, slot_room)
            div_para = ( slot_class, slot_slot, slot_batch, slot_div, CURR_BRANCH)
            all_para = ( slot_class, slot_sub, slot_slot, slot_fac, slot_room, slot_batch, CURR_BRANCH, slot_div)
            # All checks begin here
            fac_check = check_data( CURR_YEAR_SEM, fac_para=fac_para)
            div_check = check_data( CURR_YEAR_SEM, div_para=div_para)
            room_check = check_data( CURR_YEAR_SEM, room_para=room_para)
            all_check = check_data( CURR_YEAR_SEM, all_para= all_para, fac_para=fac_para, div_para=div_para,room_para=room_para)
            if(slot_sub in pass_room_subjecs):
                room_check = False
                all_check = False
            if(fac_check):
                error = error +  "Faculty has already been allotted here "
            if(div_check):
                error = error +  "Division or batch has already been allotted here "
            if(room_check):
                error = error + "Room has been allotted here " 
            if(all_check):
                error = error + "Slot might be duplicate Please Check carefully!!"
            if((not fac_check) and (not div_check) and (not room_check) and (not all_check)):
                time_query = "SELECT day,time FROM time_slots WHERE slots_name = %s"
                cursor.execute(time_query,(slot_slot,))
                time_res = cursor.fetchall()[0]
                update_query = f"INSERT INTO { CURR_YEAR_SEM }(class,subject,slot,day,time,faculty,room,batch,type,branch,division) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                update_para = (slot_class,slot_sub,slot_slot,time_res[0],time_res[1],slot_fac,slot_room,slot_batch,type_sub,CURR_BRANCH,slot_div)
                try:
                    cursor.execute(update_query,update_para)
                    conn.commit()
                    error = f"Successfully Inserted the value inTable { CURR_YEAR_SEM }"
                    return(jsonify({"error": error}),200)
                except mysql.Error as error:
                    conn.rollback()
                    return(jsonify({"error": str(error)}),400)
            return(jsonify({"error": error}),400)
    finally:
        conn.close()
        

@app.route("/view_delete_api", methods = ["POST",])
def view_delete_api():
    CURR_YEAR_SEM = session.get("curr_year_sem")
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        if request.method == "POST":
            error = ""
            del_id = request.get_json()
            delete_id = int(del_id["slot_id"])
            del_query = f"DELETE FROM { CURR_YEAR_SEM } WHERE id = %s"
            try:
                cursor.execute(del_query,(delete_id,))
                conn.commit()
                error = "Successfully deleted!"
                return(jsonify({"error": error}),200)
            except mysql.Error as error:
                return(jsonify({"error": str(error)}),400)
    finally:
        conn.close()



@app.route("/view_swap",methods = ["GET","POST"])
@login_required
def view_swap():
    CURR_BRANCH = session.get("username")
    CURR_YEAR_SEM = session.get("curr_year_sem")
    if request.method == "POST":
        return redirect("/show_timetable")
    else:
        sel_class = request.args.get("sel_class")
        infoImpo = f"Class: {sel_class}"
        complete_table = SELECT_class( sel_class, CURR_BRANCH, CURR_YEAR_SEM)
        return render_template("swap_nav.html",sel_class = sel_class,infoImpo = infoImpo,timetable = complete_table,CURR_YEAR_SEM = CURR_YEAR_SEM)
    

@app.route("/view_swap_api", methods=["POST"])
def view_swap_api():
    CURR_BRANCH = session.get("username")
    CURR_YEAR_SEM = session.get("curr_year_sem")
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        if request.method == "POST":
            # Clear temp_data table
            error = ""
            slotsInfo = request.get_json()
            slot_1 = slotsInfo["slot1"]
            slot_2 = slotsInfo["slot2"]

            # SELECT slots to be swapped
            slot_query = f"""
                SELECT class, slot, faculty, room, batch, division, subject, id, type
                FROM {CURR_YEAR_SEM} 
                WHERE id = %s OR id = %s
            """
            cursor.execute(slot_query, (slot_1, slot_2))
            slots_res = cursor.fetchall()

            slot_batch_check = []
            canInsert = []
            slot_type_check = []

            for slot in slots_res:
                slot_class, slot_slot, slot_fac, slot_room, slot_batch, slot_div, slot_sub, slot_id,slot_type = slot
                slot_type_check.append(slot_type)
                if(len(slot_type_check) >= 2):
                    if(slot_type_check[0] != slot_type_check[1]):
                        conn.rollback()
                        return jsonify({"error": "Swap cannot be done for subjects which are of different type like swap cannot be done for elective lecture with non elective lecture or tutorial with lecture!"}), 400

                slot_batch_check.append(slot_batch)

                # Check for batch swap validity
                if len(slot_batch_check) > 1:
                    if (slot_batch_check[0] != slot_batch_check[1]):
                        return jsonify({"error": "Swap cannot be done for batch with whole division or batches are different!"}), 400

                # Define parameters for checks
                div_para = (slot_class, slot_slot, slot_batch, slot_div, CURR_BRANCH)
                fac_para = (slot_slot, f"%{slot_fac}%")
                room_para = (slot_slot, slot_room)
                all_para = (slot_class, slot_sub, slot_slot, slot_fac, slot_room, slot_batch, CURR_BRANCH, slot_div)

                # Perform checks
                fac_check = check_data(CURR_YEAR_SEM, fac_para=fac_para)
                div_check = check_data(CURR_YEAR_SEM, div_para=div_para)
                room_check = check_data(CURR_YEAR_SEM, room_para=room_para)
                all_check = check_data(CURR_YEAR_SEM, all_para=all_para, fac_para=fac_para, div_para=div_para, room_para=room_para)

                # Handle errors
                if len(fac_check) > 1:
                    error += "Faculty has already been allotted here. "
                    canInsert = []
                    break
                if len(div_check) > 1:
                    error += "Division or batch has already been allotted here. "
                    canInsert = []
                    break
                if len(room_check) > 1:
                    error += "Room has been allotted here. "
                    canInsert = []
                    break
                if len(all_check) > 1:
                    error += "Slot might be duplicate. Please check carefully! "
                    canInsert = []
                    break

                if not (len(fac_check) > 1) and not (len(div_check) > 1) and not (len(room_check) > 1) and not (len(all_check) > 1):
                    get_time = "SELECT day,time FROM time_slots WHERE slots_name = %s"
                    cursor.execute(get_time,(slot_slot,))
                    time_res  = cursor.fetchall()[0]
                    canInsert.append((slot_slot,time_res[0],time_res[1],slot_id))         
            if len(canInsert) == 2:
                id1, id2 = canInsert[0][-1],canInsert[1][-1]


                update_query = f"""
                    UPDATE {CURR_YEAR_SEM} SET slot = %s,day = %s,time = %s
                    WHERE id = %s
                """

                try:
                    cursor.execute(update_query, (canInsert[0][0],canInsert[0][1],canInsert[0][2],id2))
                    cursor.execute(update_query, (canInsert[1][0],canInsert[1][1],canInsert[1][2],id1))
                    conn.commit()
                    error = "Successfully Swapped!"
                    return jsonify({"error": error}), 200
                except mysql.Error as errors:
                    conn.rollback()
                    return jsonify({"error": str(errors)}), 400
            else:
                conn.rollback()
                return jsonify({"error": error}), 400
    finally:
        conn.close()



@app.route("/free_faculty", methods=["GET","POST"])
@login_required
def free_faculty():
    CURR_BRANCH = session.get("username")
    CURR_YEAR_SEM = session.get("curr_year_sem")
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        if request.method == "POST":
            department = request.form.get("sel_dept")
            daysInDict = { "Monday" :'A' ,"Tuesday" : 'B', "Wednesday" : "C" , "Thursday": 'D', "Friday" : 'E'}
            time_slots = ["7:00-8:00","8:00-9:00", "9:00-10:00", "10:00-11:00", "11:00-12:00","12:00-1:00", "1:00-2:00", "2:00-3:00", "3:00-4:00", "4:00-5:00", "5:00-6:00", "6:00-7:00"]
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            table_head = "<thead><tr><th>Time/Day</th>"
            for day in days:
                table_head = table_head + f"<th>{day}</th>"
            table_head = table_head + "</tr></thead>"
            table_body = "<tbody>"
            for t in range(len(time_slots)):
                table_body = table_body + f"<tr><td class='timeslot' style='text-align: center;'>{time_slots[t]}</td>"
                if(time_slots[t] == "1:00-2:00"):
                    table_body = table_body + f'<td colspan=5 style="text-align: center;" class="lunch">LUNCH BREAK</td>'
                    continue
                for day in days:
                    get_free_room_query = f"SELECT facinit FROM faculty WHERE facinit NOT IN (SELECT faculty FROM {CURR_YEAR_SEM} WHERE day = %s AND time = %s and(facdep = %s or facshdep = %s))"
                    get_free_room_para = (day,time_slots[t],department,department)
                    cursor.execute(get_free_room_query,get_free_room_para)
                    free_room_data = cursor.fetchall()
                    free_rooms = ""
                    for room_data in free_room_data:
                        free_rooms = free_rooms + room_data[0] + ","
                    td = f"<td colspan=1>{free_rooms}</td>"
                    table_body = table_body + td
                table_body = table_body + "</tr>"
            table_body = table_body + "</tbody>"
            complete_table = table_head + table_body
            users_query = f"SELECT username FROM users"
            cursor.execute(users_query)
            users_data = cursor.fetchall()
            return render_template("free_faculty.html",timetable = complete_table,department_res = users_data)
        else:
            users_query = f"SELECT username FROM users"
            cursor.execute(users_query)
            users_data = cursor.fetchall()
            return render_template("free_faculty.html",department_res = users_data)
    finally:
        conn.close()

@app.route("/free_room", methods=["GET"])
@login_required
def free_room():
    CURR_BRANCH = session.get("username")
    CURR_YEAR_SEM = session.get("curr_year_sem")
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    try:
        if request.method == "GET":
            daysInDict = { "Monday" :'A' ,"Tuesday" : 'B', "Wednesday" : "C" , "Thursday": 'D', "Friday" : 'E'}
            time_slots = ["7:00-8:00","8:00-9:00", "9:00-10:00", "10:00-11:00", "11:00-12:00","12:00-1:00", "1:00-2:00", "2:00-3:00", "3:00-4:00", "4:00-5:00", "5:00-6:00", "6:00-7:00"]
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            table_head = "<thead><tr><th>Time/Day</th>"
            for day in days:
                table_head = table_head + f"<th>{day}</th>"
            table_head = table_head + "</tr></thead>"
            table_body = "<tbody>"
            for t in range(len(time_slots)):
                table_body = table_body + f"<tr><td class='timeslot' style='text-align: center;'>{time_slots[t]}</td>"
                if(time_slots[t] == "1:00-2:00"):
                    table_body = table_body + f'<td colspan=5 style="text-align: center;" class="lunch">LUNCH BREAK</td>'
                    continue
                for day in days:
                    get_free_room_query = f"SELECT roomno FROM rooms WHERE roomno NOT IN (SELECT room FROM {CURR_YEAR_SEM} WHERE day = %s AND time = %s)"
                    get_free_room_para = (day,time_slots[t],)
                    cursor.execute(get_free_room_query,get_free_room_para)
                    free_room_data = cursor.fetchall()
                    free_rooms = ""
                    for room_data in free_room_data:
                        free_rooms = free_rooms + room_data[0] + ","
                    td = f"<td colspan=1>{free_rooms}</td>"
                    table_body = table_body + td
                table_body = table_body + "</tr>"
            table_body = table_body + "</tbody>"
            complete_table = table_head + table_body
            return render_template("free_room.html",timetable = complete_table)
    finally:
        conn.close()

@app.route("/all_faculty_info", methods=["GET"])
@login_required
def all_faculty_info():
    CURR_BRANCH = session.get("username")
    CURR_YEAR_SEM = session.get("curr_year_sem")
    conn = mysql.connect(**config)
    cursor = conn.cursor()
    table_head = "<thead><tr><th>Faculty Initials</th><th>Faculty Name</th><th>Faculty Load</th><th>Total Load</th></tr></thead>"
    try:
        if request.method == "GET":
            table_body = "<tbody>"
            get_facinit_query = "SELECT facinit,facname FROM faculty"
            cursor.execute(get_facinit_query)
            facinit_data = cursor.fetchall()
            for faculty_init in facinit_data:
                subject_query = f"SELECT DISTINCT(subject) FROM {CURR_YEAR_SEM} WHERE faculty = %s"
                cursor.execute(subject_query,(faculty_init[0],))
                subject_data = cursor.fetchall()
                total_load = 0
                table_body = table_body + f"<tr><td>{faculty_init[0]}</td><td>{faculty_init[1]}</td><td>"
                for subject in subject_data:
                    sub_para = (f"%{faculty_init[0]}%",subject[0])
                    lec_load_query = f"""SELECT 
                                        COUNT(*) as count
                                    FROM (
                                        SELECT
                                            subject, 
                                            slot, 
                                            day, 
                                            time, 
                                            faculty, 
                                            room,  
                                            type
                                        FROM 
                                            {CURR_YEAR_SEM}
                                        WHERE faculty LIKE %s and type LIKE "%L%" and subject = %s
                                        GROUP BY
                                            subject, 
                                            slot, 
                                            day, 
                                            time, 
                                            faculty, 
                                            room, 
                                            type
                                    ) as unique_rows;"""
                    prac_load_query = f"""SELECT 
                                        COUNT(*) as count
                                    FROM (
                                        SELECT
                                            subject, 
                                            slot, 
                                            day, 
                                            time, 
                                            faculty, 
                                            room, 
                                            type
                                        FROM 
                                            {CURR_YEAR_SEM}
                                        WHERE faculty LIKE %s and type LIKE "%P%" and subject = %s
                                        GROUP BY
                                            subject, 
                                            slot, 
                                            day, 
                                            time, 
                                            faculty, 
                                            room,
                                            type
                                    ) as unique_rows;"""
                    tut_load_query = f"""SELECT 
                                        COUNT(*) as count
                                    FROM (
                                        SELECT 
                                            subject, 
                                            slot, 
                                            day, 
                                            time, 
                                            faculty, 
                                            room,
                                            type
                                        FROM 
                                            {CURR_YEAR_SEM}
                                        WHERE faculty LIKE %s and type LIKE "%T%" and subject = %s
                                        GROUP BY 
                                            subject, 
                                            slot, 
                                            day, 
                                            time, 
                                            faculty, 
                                            room, 
                                            type
                                    ) as unique_rows;"""
                    cursor.execute(lec_load_query,sub_para)
                    lec_load = cursor.fetchall()[0][0]
                    cursor.execute(prac_load_query,sub_para)
                    prac_load = cursor.fetchall()[0][0]
                    cursor.execute(tut_load_query,sub_para)
                    tut_load = cursor.fetchall()[0][0]
                    subject_total_load = lec_load + tut_load + prac_load
                    total_load = total_load + subject_total_load
                    table_body = table_body + f"{subject[0]} {subject_total_load} <br>"
                table_body = table_body + f"</td><td>{total_load}</td></tr>"
            table_body = table_body + "</tbody>"
            complete_table = table_head + table_body
            return render_template("all_faculty_info.html",timetable = complete_table)
    finally:
        conn.close()

            
