'''
Generate Actuals on Deadline
Alican Sesli - LUX VFX - 03.12.2019
Generates actuals based on selected shots/tasks on Deadline
    v1: Actuals deadline counterpart..makin it work.
    v2: Fixed error when only one task is selected
    v3: out location
'''

import os, sys
import subprocess

print('Python Version: ', sys.version)

sys.path.insert(0, "\\\\qumulo\\Libraries\\python-lib\\FTRACK")
import ftrack_api

sys.path.insert(0, "\\\\qumulo\\Libraries\\python-lib")
import imageio
import scipy.misc

from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

import getpass


sys.path.insert(0, "L:\\HAL\\LIVEAPPS\\apps\\Scripts\\FTRACK\\python-lib\\Lib")


import xlsxwriter
from datetime import datetime

selection_d = sys.argv[1]

selection_d = eval(selection_d)

user = selection_d['user']
selection = selection_d['selection']
out_file = selection_d['out_file']


os.environ['FTRACK_API_USER'] = user

FTRACK_URL = 'https://domain.ftrackapp.com'
FTRACK_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

os.environ['FTRACK_SERVER'] = FTRACK_URL
os.environ['FTRACK_API_KEY'] = FTRACK_KEY


session = ftrack_api.session.Session(auto_connect_event_hub=True)


def create_sheet(file,logs,users,tasks):
    '''Creates acutals spreadsheet file(A:/full/path/file.xls) by processing logs(dictionary), users(dictionary) and tasks(dictionary)'''
    '''
    logs = {
        'BEY201_001_010' : {
            tasks : {
                'Compositing' : {
                    timelogs : {
                        'yashg' : duration,
                        'johnm' : duration
                    },
                    stats : {
                        bid : 1,
                        duration : 120,
                        difficulty : 2,
                        iterations : 9
                    }
                }
            },
            stats : {
                description: Complex clean up,
                status: Client Approved,
                duration : 120,
            }
        }
    }'''
    '''
    users = {
        luxali:{
            first_log:'date',
            last_log:'date'
        }
    }


    '''
    #gather artist related bids + costs
    def _from_YX(y, x):
        abc = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        #return '{0}{1}'.format(abc[x], y)
        a = '{0}{1}'.format(abc[x], y)
        a = a.upper()
        #print a
        return a
    #print users

    shots = sorted(logs.keys())

    #for shot in shots:
    #    print shot, logs[shot]

    workbook = xlsxwriter.Workbook(file)

    worksheet = workbook.add_worksheet('actuals')
    usersheet = workbook.add_worksheet('users')
    tasksheet = workbook.add_worksheet('tasks')


    # Set up some formats to use.
    bold = workbook.add_format({'bold': True})
    italic = workbook.add_format({'italic': True})
    red = workbook.add_format({'color': 'red'})
    blue = workbook.add_format({'color': 'blue'})
    center = workbook.add_format({'align': 'center'})
    superscript = workbook.add_format({'font_script': 1})
    #cell_format = workbook.add_format()
    #cell_format = cell_format.set_bg_color('green')
    title_format = workbook.add_format({'bold': True, 'bg_color': 'C9C9C9', 'top':True, 'bottom':True})
    title_format_labels = workbook.add_format({'bold': True,'italic': True,'size': 8,'align':'right','font_color':'6E6E6E', 'bg_color': 'C9C9C9', 'top':True, 'bottom':True})
    total_format = workbook.add_format({'bold': True, 'italic': True,'align':'right'})
    input_format = workbook.add_format({'bold': True, 'font_color': 'blue'})
    #print user_dict



    ##########USERS

    current_row = 0
    current_col = 0

    user_dict = {}
    user_total_hours = {}
    user_bid = {}
    user_bid_cost = {}
    user_avg_iterations = {}
    user_avg_difficulty = {}

    tasks_count = {}
    tasks_dict = {}
    task_total_hours = {}
    tasks_total_cost = {}
    task_bid = {}
    task_bid_cost = {}
    tasks_total_bid_days = {}
    user_task_bid_str = {}
    tasks_total_hours = {}
    #############################################################################################

    usersheet.write(current_row, 0, 'artist', title_format_labels )
    usersheet.write(current_row, 1, 'rate/hr', title_format_labels )
    usersheet.write(current_row, 2, 'Actual Hours', title_format_labels )
    usersheet.write(current_row, 3, 'Actual Cost', title_format_labels )
    usersheet.write(current_row, 4, 'Associated Bid Days', title_format_labels )
    usersheet.write(current_row, 5, 'Associated Bid Cost', title_format_labels )
    usersheet.write(current_row, 6, 'logged tasks', title_format_labels )
    usersheet.write(current_row, 7, 'avg. hr/task', title_format_labels )
    usersheet.write(current_row, 8, 'avg. cost/task', title_format_labels )
    usersheet.write(current_row, 9, 'iterations/shot', title_format_labels )
    usersheet.write(current_row, 10, 'avg. Task difficulty', title_format_labels )
    usersheet.write(current_row, 11, 'easiest', title_format_labels )
    usersheet.write(current_row, 12, 'hardest', title_format_labels )
    usersheet.write(current_row, 13, 'first log', title_format_labels )
    usersheet.write(current_row, 14, 'last log', title_format_labels )
    usersheet.write(current_row, 15, 'avg. Day (hr)', title_format_labels )
    usersheet.write(current_row, 16, 'task level totals', title_format_labels )
    usersheet.freeze_panes(0, 1)

    current_row+=1
    user_hours ='='

    #Process the user input
    for user in users:
        default_rate = 0.0
        usersheet.write(current_row, 0, user, bold)
        usersheet.write(current_row, 1, default_rate, input_format)
        current_row+=1
        usersheet.write_formula(_from_YX(current_row,3), '=B{0}*C{0}'.format(current_row) )
        usersheet.write_formula(_from_YX(current_row,7), '=C{0}/G{0}'.format(current_row) )
        usersheet.write_formula(_from_YX(current_row,8), '=B{0}*H{0}'.format(current_row) )
        user_dict[user]=_from_YX(current_row,1)


    current_row+=2
    usersheet.write_formula(_from_YX(current_row,1), '=SUM(B2:B{0})'.format(str(len(users)+1)), total_format)
    usersheet.write_formula(_from_YX(current_row,2), '=SUM(C2:C{0})'.format(str(len(users)+1)), total_format)
    usersheet.write_formula(_from_YX(current_row,3), '=SUM(D2:D{0})'.format(str(len(users)+1)), total_format)
    usersheet.write_formula(_from_YX(current_row,4), '=SUM(E2:E{0})'.format(str(len(users)+1)), total_format)
    usersheet.write_formula(_from_YX(current_row,5), '=SUM(F2:F{0})'.format(str(len(users)+1)), total_format)
    usersheet.write_formula(_from_YX(current_row,7), '=AVERAGE(H2:H{0})'.format(str(len(users)+1)), total_format)
    usersheet.write_formula(_from_YX(current_row,8), '=AVERAGE(I2:I{0})'.format(str(len(users)+1)), total_format)
    usersheet.write_formula(_from_YX(current_row,9), '=AVERAGE(J2:J{0})'.format(str(len(users)+1)), total_format)
    usersheet.write_formula(_from_YX(current_row,10), '=AVERAGE(K2:K{0})'.format(str(len(users)+1)), total_format)


    chart1 = workbook.add_chart({'type': 'bar'})
    chart1.add_series({
        #'name':       '=users!$B$1',
        'categories': '=users!$A$2:$A${}'.format(str(len(users)+1)),
        'values':     '=users!$B$2:$B${}'.format(str(len(users)+1)),
        'fill': {'transparency':50},
    })
    chart1.set_chartarea({'fill': {'color': 'white', 'transparency': 100}})
    chart1.set_plotarea({'fill': {'color': 'white', 'transparency': 100},'layout': {'x': 0.0,'y': 0.0,'width': 1,'height': 1,}})
    chart1.set_y_axis({'reverse': True, 'major_gridlines': {'visible': False},'visible': False})
    chart1.set_x_axis({'major_gridlines': {'visible': False},'label_position': 'high'})
    chart1.set_legend({'none': True})
    #usersheet.insert_chart('B2', chart1, {'x_offset': -6, 'y_offset': -6,'x_scale': 0.145, 'y_scale': 0.085*(len(users))})

    ###########TASKS


    current_row = 0
    current_col = 0

    tasksheet.write(current_row, 0, 'task', title_format_labels )
    tasksheet.write(current_row, 1, 'cost', title_format_labels )
    tasksheet.write(current_row, 2, 'Actual Hours', title_format_labels )
    tasksheet.write(current_row, 3, 'Actual Cost', title_format_labels )
    tasksheet.write(current_row, 4, 'Bid Days', title_format_labels )
    tasksheet.write(current_row, 5, 'Bid Cost', title_format_labels )
    tasksheet.write(current_row, 6, '# of Tasks', title_format_labels )
    tasksheet.write(current_row, 7, 'avg. hr/task', title_format_labels )
    #tasksheet.write(current_row, 8, 'first log', title_format_labels )
    #tasksheet.write(current_row, 9, 'last log', title_format_labels )
    #tasksheet.write(current_row, 10, 'avg. Day (hr)', title_format_labels )
    #tasksheet.write(current_row, 11, 'avg. Task difficulty', title_format_labels )
    #asksheet.write(current_row, 12, 'task level totals', title_format_labels )
    tasksheet.freeze_panes(0, 1)

    current_row+=1

    
    #Process the tasks input
    for task in tasks:
        default_rate = 0.0
        tasksheet.write(current_row, 0, task, bold)
        tasksheet.write(current_row, 1, default_rate, input_format)
        current_row+=1
        #current_row+=1
        #task_dict[task]=_from_YX(current_row,1)
        #default_rate = 0.0
        #usersheet.write(current_row, 0, user )
        #usersheet.write(current_row, 1, default_rate )
        #current_row+=1
        #tasksheet.write_formula(_from_YX(current_row,3), '=B{0}*C{0}'.format(current_row) )
        tasksheet.write_formula(_from_YX(current_row,5), '=B{0}*E{0}'.format(current_row) )
        tasksheet.write_formula(_from_YX(current_row,7), '=C{0}/G{0}'.format(current_row) )

        tasks_dict[task]=_from_YX(current_row,1)

    current_row+=2
    tasksheet.write_formula(_from_YX(current_row,2), '=SUM(C2:C{0})'.format(str(len(tasks)+1)), total_format)
    tasksheet.write_formula(_from_YX(current_row,3), '=SUM(D2:D{0})'.format(str(len(tasks)+1)), total_format)
    tasksheet.write_formula(_from_YX(current_row,4), '=SUM(E2:E{0})'.format(str(len(tasks)+1)), total_format)
    tasksheet.write_formula(_from_YX(current_row,5), '=SUM(F2:F{0})'.format(str(len(tasks)+1)), total_format)
    tasksheet.write_formula(_from_YX(current_row,6), '=SUM(G2:G{0})'.format(str(len(tasks)+1)), total_format)
    #tasksheet.write_formula(_from_YX(current_row,7), '=AVERAGE(H2:H{0})'.format(str(len(tasks)+1)), total_format)

    ##########ACTUALS

    formater = workbook.add_format({'left':1})
    worksheet.set_column(2, 2, 10, formater)
    worksheet.set_column(5, 5, 10, formater)
    worksheet.set_column(8, 8, 10, formater)
    worksheet.set_column(12, 12, 10, formater)
    worksheet.set_column(13, 13, 10, formater)
    # Widen the first column to make the text clearer.
    worksheet.set_column('A:A', 15)
    worksheet.set_column('L:L', 17)
    worksheet.set_column('M:M', 17)
    worksheet.freeze_panes(0, 1)

    actual_totals_list =[]
    bid_totals_list = []
    current_row = 0
    current_col = 0

    for shot in shots:

        #print shot, logs[shot]

        shot_rows = 1
        shot_cols = 5
        current_col = 0
        #worksheet.write(current_row, 0, shot)
        worksheet.write(current_row, 0, shot, title_format )
        worksheet.write(current_row, 1, 'artist', title_format_labels )
        worksheet.write(current_row, 2, 'hours', title_format_labels )
        worksheet.write(current_row, 3, 'rate/hr', title_format_labels )
        worksheet.write(current_row, 4, '', title_format_labels )
        worksheet.write(current_row, 5, 'bid(days)', title_format_labels )
        worksheet.write(current_row, 6, 'rate/day', title_format_labels )
        worksheet.write(current_row, 7, '', title_format_labels )
        worksheet.write(current_row, 8, 'iterations', title_format_labels )
        worksheet.write(current_row, 9, 'difficulty', title_format_labels )
        worksheet.write(current_row, 10, 'duration', title_format_labels )
        worksheet.write(current_row, 11, 'status', title_format_labels )
        worksheet.write(current_row, 12, 'description', title_format_labels )
        worksheet.write(current_row, 13, 'graph', title_format_labels )
        #worksheet.write(current_row, 0, shot, title_format )
        #worksheet.write_rich_string(_from_YX(current_row, 0),bold, shot)
        #worksheet.write_rich_string('A0',bold, shot)
        current_row+=1

        shot_tasks = logs[shot]['tasks'].keys()
        shot_stats = logs[shot]['stats'].keys()


        sum_cells = "="
        sum_bid_cells = '='
        for task in shot_tasks:

            #print logs[shot][task]['timelogs']
            #timelog_len = len(logs[shot][task]['timelogs'])

            worksheet.write(current_row, 0, task)
            worksheet.write(current_row, 2, 0)
            worksheet.write(current_row, 3, 0)
            worksheet.write_formula(_from_YX(current_row+1, 4), "=D{0}*C{0}".format(current_row+1) )
            current_col+=1
            task_users = logs[shot]['tasks'][task]['timelogs'].keys()


            ###print logs[shot][task]['timelogs']

            status  = logs[shot]['tasks'][task]['stats']['status']


            #### TASKS.
            temp_col = current_col
            temp_row = current_row

            current_col = temp_col
            current_row = temp_row


            #### BID ENTRY GETS CREATED WEIRDLY
            temp_col = current_col
            temp_row = current_row
            current_col = 5
            current_row+=1

            bid = logs[shot]['tasks'][task]['stats']['bid']
            task_users_len = len(task_users)

            user_bid_days_cell = _from_YX(current_row, current_col)
            user_bid_days_exp = "'actuals'!"+user_bid_days_cell+'/'+str(max(task_users_len,1))
            user_bid_days_exp = user_bid_days_exp.replace('/1','')

            user_bid_cost_exp = user_bid_days_exp + '*' + "'tasks'!{}".format(tasks_dict[task])

            task_iterations_cell = _from_YX(current_row, current_col+3)
            user_iterations_exp = "'actuals'!"+task_iterations_cell+'/'+str(max(task_users_len,1))
            user_iterations_exp = user_iterations_exp.replace('/1','')

            task_difficulty_cell = _from_YX(current_row, current_col+4)
            user_difficulty_exp = "'actuals'!"+task_difficulty_cell
            

            #print
            #print user_bid_days_exp
            #print
            #print user_bid_cost_exp

            worksheet.write(_from_YX(current_row, current_col), bid, blue)
            #user_bid_
            current_col+=1
            worksheet.write_formula(_from_YX(current_row, current_col), "='tasks'!{}".format(tasks_dict[task]) )
            current_col+=1
            worksheet.write_formula(_from_YX(current_row, current_col), '={}*{}'.format(_from_YX(current_row,current_col-1),_from_YX(current_row,current_col-2)))
            sum_bid_cells+= '+'+_from_YX(current_row, current_col)
            current_col = 11
            worksheet.write(_from_YX(current_row, current_col), status)

            current_col = temp_col
            current_row = temp_row


            #### STATS ENTRY GETS CREATED WEIRDLY
            temp_col = current_col
            temp_row = current_row
            current_col = 8
            current_row+=1

            
            iterations = logs[shot]['tasks'][task]['stats']['iterations']
            worksheet.write(_from_YX(current_row, current_col), iterations)
            current_col+=1

            difficulty = logs[shot]['tasks'][task]['stats']['difficulty']
            worksheet.write(_from_YX(current_row, current_col), difficulty)
            current_col+=1

            duration   = logs[shot]['tasks'][task]['stats']['duration']
            worksheet.write(_from_YX(current_row, current_col), duration)
            current_col+=1

            #worksheet.write(_from_YX(current_row, current_col), bid)
            #current_col+=1
            #worksheet.write_formula(_from_YX(current_row, current_col), "='tasks'!{}".format(task_dict[task]) )
            #current_col+=1
            #worksheet.write_formula(_from_YX(current_row, current_col), '={}*{}'.format(_from_YX(current_row,current_col-1),_from_YX(current_row,current_col-2)))
            #sum_bid_cells+= '+'+_from_YX(current_row, current_col)
            current_col = temp_col
            current_row = temp_row

            if task not in tasks_total_hours.keys():
                tasks_total_hours[task] = []

            if task not in tasks_total_cost.keys():
                tasks_total_cost[task] = []

            if task not in tasks_total_bid_days.keys():
                tasks_total_bid_days[task] = []

            if task not in tasks_count.keys():
                tasks_count[task] = 0
            tasks_count[task] +=1

            tasks_total_cost[task].append(_from_YX(current_row+1, current_col+3))


            if task_users:
                for u in task_users:
                    #print u
                    
                    worksheet.write(_from_YX(current_row+1, current_col), u)
                    current_col+=1
                    worksheet.write(_from_YX(current_row+1, current_col), logs[shot]['tasks'][task]['timelogs'][u],blue)
                    current_col+=1
                    #worksheet.write(current_row, current_col, 240.00)
                    #print user_dict[u]
                    worksheet.write_formula(_from_YX(current_row+1, current_col), "='users'!{}".format(user_dict[u]) )
                    #worksheet.write(current_row, current_col, '=users.B4'.format(user_dict[u])) 
                    current_col+=1
                    #worksheet.write(current_row, current_col, 'result')
                    worksheet.write_formula(_from_YX(current_row+1, current_col), '={}*{}'.format(_from_YX(current_row+1,current_col-1),_from_YX(current_row+1,current_col-2)))
                    
                    
                    artist_hours_str = _from_YX(current_row+1,current_col-2)

                    if u not in user_total_hours.keys():
                        user_total_hours[u]=[]

                    user_total_hours[u].append(artist_hours_str)


                    sum_cells+= '+'+_from_YX(current_row+1, current_col)

                    current_col=1
                    current_row+=1

                    ####user bid = appended bid days for each artist to a dict
                    #user_bid_cost_exp


                    if u not in user_bid.keys():
                        user_bid[u] = []
                    #else:
                    user_bid[u].append(user_bid_days_exp)


                    if u not in user_bid_cost.keys():
                        user_bid_cost[u] = []

                    #else:
                    user_bid_cost[u].append(user_bid_cost_exp)

                    if u not in user_avg_iterations.keys():
                        user_avg_iterations[u] = []
                    #else:
                    user_avg_iterations[u].append(user_iterations_exp)


                    if u not in user_avg_difficulty.keys():
                        user_avg_difficulty[u] = []
                    #else:
                    user_avg_difficulty[u].append(user_difficulty_exp)

                    #append C total hours
                    tasks_total_hours[task].append(_from_YX(current_row, current_col+1))
                    #append E subtotals
                    #tasks_total_cost[task].append(_from_YX(current_row, current_col+3))
                    #append F bid(days)
                    tasks_total_bid_days[task].append(_from_YX(current_row, current_col+4))

                    
            else:
                current_row+=1



            current_col = 0
        
        #for stat in shot_stats:
        description = logs[shot]['stats']['description']
        worksheet.write(current_row-1, 12, description)
        
        current_col = 3
        worksheet.write(_from_YX(current_row+1, current_col), 'ACTUAL:', total_format)
        current_col +=1
        worksheet.write_formula(_from_YX(current_row+1, current_col), sum_cells, bold)
        actual_totals_list.append(_from_YX(current_row+1, current_col))

        current_col = 6
        worksheet.write(_from_YX(current_row+1, current_col), 'BID:', total_format)
        current_col +=1
        worksheet.write_formula(_from_YX(current_row+1, current_col), sum_bid_cells, bold)
        bid_totals_list.append(_from_YX(current_row+1, current_col))
        current_col = 0
        current_row+=1


    current_row+=2


    worksheet.write(_from_YX(current_row, 0), "{} SHOTS".format(len(shots)), total_format)
    
    worksheet.write(_from_YX(current_row, 1), "{} USERS".format(len(users)), total_format)

    actual_totals_list = '+'.join(actual_totals_list)
    worksheet.write(_from_YX(current_row, 3), "ACTUAL TOTAL", total_format)
    worksheet.write_formula(_from_YX(current_row, 4), actual_totals_list, bold)

    bid_totals_list = '+'.join(bid_totals_list)
    worksheet.write(_from_YX(current_row, 6), "BID TOTAL", total_format)
    worksheet.write_formula(_from_YX(current_row, 7), bid_totals_list, bold)
    #xxformat = workbook.add_format()
    #xxformat.set_right(1)


    worksheet_row = current_row
    worksheet_col = current_col
    #####REPOPULATE USERS
    #user_bid[u] contains an arary of cell entires/num of tasks
    for u in user_dict.keys():
        user_cell = user_dict[u].replace('B','A')
        #sets the total hours
        total_hours_formula =["'actuals'!{}".format(i) for i in user_total_hours[u]]
        total_hours_formula = '+'.join(total_hours_formula)
        total_hours_formula = '='+total_hours_formula
        usersheet.write_formula(user_cell.replace('A','C'),total_hours_formula)
        usersheet.write(user_cell.replace('A','G') , len(user_total_hours[u]))
        #print user_bid[u]
        bid_days_formula = '+'.join(user_bid[u])
        bid_days_formula = '=' + bid_days_formula
        usersheet.write(user_cell.replace('A','E') , bid_days_formula)
        bid_cost_formula = '+'.join(user_bid_cost[u])
        bid_cost_formula = '=' + bid_cost_formula
        usersheet.write(user_cell.replace('A','F') , bid_cost_formula)

        iterations_formula = ','.join(user_avg_iterations[u])
        iterations_formula = '=AVERAGE(' + iterations_formula + ')'
        usersheet.write(user_cell.replace('A','J') , iterations_formula)

        difficulty_formula = ','.join(user_avg_difficulty[u])
        difficulty_formula = '=AVERAGE(' + difficulty_formula + ')'
        usersheet.write(user_cell.replace('A','K') , difficulty_formula)
        
    for t in tasks_dict.keys():
        task_cell = tasks_dict[t].replace('B','A')
        #sets the total hours
        total_hours_formula =["'actuals'!{}".format(i) for i in tasks_total_hours[t]]
        total_hours_formula = '+'.join(total_hours_formula)
        total_hours_formula = '='+total_hours_formula
        tasksheet.write_formula(task_cell.replace('A','C'),total_hours_formula)

        total_cost_formula =["'actuals'!{}".format(i) for i in tasks_total_cost[t]]
        total_cost_formula = '+'.join(total_cost_formula)
        total_cost_formula = '='+total_cost_formula
        tasksheet.write_formula(task_cell.replace('A','D'),total_cost_formula)


        total_bid_days_formula =["'actuals'!{}".format(i) for i in tasks_total_bid_days[t]]
        total_bid_days_formula = '+'.join(total_bid_days_formula)
        total_bid_days_formula = '='+total_bid_days_formula
        tasksheet.write_formula(task_cell.replace('A','E'),total_bid_days_formula)
        tasksheet.write(task_cell.replace('A','G') , tasks_count[t])
        

    workbook.close()

    return


def merge_two_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z


msg = 'Actuals'
t_logs = {}
users = []
tasks_list = []
task_ids = []
tasks = []
_t_logs = {}

for entity in selection:

    entityId = entity['entityId']
    
    tids_querry = session.query('select id from Task where ancestors.id is "{0}" or project_id is "{0}" or id is "{0}"'.format(entityId)).all()
    
    if tids_querry:
        for tid in tids_querry:
            tid = tid['id']
            if tid not in task_ids:
                task_ids.append(str(tid))

task_ids = list(set(task_ids))

#print task_ids

parent = session.query('select parent.parent from Task where id is "{}"'.format(task_ids[0])).first()

path = parent['custom_attributes']['base_path']

path = path + '03_COORDINATION/'

task_chunks = [tuple(task_ids)]
tasks_len = len(task_ids)
progress = 0.0
progress_inc = 100.0/float(tasks_len)
num = 0

print  '{0} tasks'.format(tasks_len)

for task_chunk in task_chunks:

    if tasks_len >1:
        tasks = session.query('select custom_attributes, id, object_type.name, name, parent from Task where id in {0}'.format(task_chunk)).all()
    else:
        tasks = session.query('select custom_attributes, id, object_type.name, name, parent from Task where id is {0}'.format(task_chunk[0])).all()

    num+=len(tasks)
    for task in tasks:

        shot_name = task['parent']['name']
        task_type = task['type']['name']
        timelogs  = task['timelogs']
        bid = (task['bid']/3600)/8#Seconds>Days >>> then normalize 0-8 to 0-1
        iterations = task['custom_attributes']['review_counter']
        difficulty = task['custom_attributes']['difficulty']
        object_type = task['parent']['object_type']['name']
        duration = 0
        if object_type == 'Shot':
            duration = task['parent']['custom_attributes']['Duration (frames)']
        status =  task['status']['name']
        description = task['parent']['description']


        print u'{}'.format(shot_name), u'{}'.format(task_type)#, u'{}'.format(timelogs), u'{}'.format(bid), u'{}'.format(iterations), u'{}'.format(difficulty), u'{}'.format(object_type), u'{}'.format(duration), u'{}'.format(status), u'{}'.format(description)

        tasks_list.append(task_type)

        #
        #logs = {
        #    'BEY201_001_010' : {
        #        tasks : {
        #            'Compositing' : {
        #                timelogs : {
        #                    'yashg' : duration,
        #                    'johnm' : duration
        #                },
        #                stats : {
        #                    bid : 1,
        #                    duration : 120,
        #                    difficulty : 2,
        #                    iterations : 9
        #                }
        #            }
        #        },
        #       stats : {
        #           description: Complex clean up,
        #           status: Client Approved,
        #           duration : 120,
        #        }
        #    }
        #}
        
        if shot_name not in t_logs.keys():
            t_logs[shot_name] = {}

        if 'tasks' not in t_logs[shot_name].keys():
            t_logs[shot_name]['tasks'] = {}

        if 'stats' not in t_logs[shot_name].keys():
            t_logs[shot_name]['stats'] = {}

        #if 'status' not in t_logs[shot_name]['stats'].keys():
        #    t_logs[shot_name]['stats']['status'] = shot_status

        if 'description' not in t_logs[shot_name]['stats'].keys():
            t_logs[shot_name]['stats']['description'] = description
        #t_logs[shot_name]['stats']['description'] = description
        if task_type not in t_logs[shot_name]['tasks'].keys():
            t_logs[shot_name]['tasks'][task_type] = {}

        if 'timelogs' not in t_logs[shot_name]['tasks'][task_type].keys():
            t_logs[shot_name]['tasks'][task_type]['timelogs'] = {}

        if 'stats' not in t_logs[shot_name]['tasks'][task_type].keys():
            t_logs[shot_name]['tasks'][task_type]['stats'] = {}

        if 'bid' in t_logs[shot_name]['tasks'][task_type]['stats'].keys():
            t_logs[shot_name]['tasks'][task_type]['stats']['bid'] = t_logs[shot_name]['tasks'][task_type]['stats']['bid']+bid
        else:
            t_logs[shot_name]['tasks'][task_type]['stats']['bid'] = bid

        if 'iterations' in t_logs[shot_name]['tasks'][task_type]['stats'].keys():
            t_logs[shot_name]['tasks'][task_type]['stats']['iterations'] = int(t_logs[shot_name]['tasks'][task_type]['stats']['iterations']+iterations)
        else:
            t_logs[shot_name]['tasks'][task_type]['stats']['iterations'] = int(iterations)

        if 'difficulty' in t_logs[shot_name]['tasks'][task_type]['stats'].keys():
            t_logs[shot_name]['tasks'][task_type]['stats']['difficulty'] = max(t_logs[shot_name]['tasks'][task_type]['stats']['difficulty'],difficulty)
        else:
            t_logs[shot_name]['tasks'][task_type]['stats']['difficulty'] = difficulty

        if 'duration' not in t_logs[shot_name]['tasks'][task_type]['stats'].keys():
            t_logs[shot_name]['tasks'][task_type]['stats']['duration'] = duration

        if 'status' not in t_logs[shot_name]['tasks'][task_type]['stats'].keys():
            t_logs[shot_name]['tasks'][task_type]['stats']['status'] = status
        
        #start_date = timelogs[0]

        for t in timelogs:

            t_dur   = float(t['duration'])#seconds
            t_dur   = t_dur/3600#hours
            t_dur   = round(t_dur,3)
            if t.get('user'):
                t_username = t['user']['username']
            else:
                t_username = 'Unknown'
            users.append(t_username)
            #t_dict  = {t_username:t_dur}
            
            if t_username in t_logs[shot_name]['tasks'][task_type]['timelogs'].keys():
                t_logs[shot_name]['tasks'][task_type]['timelogs'][t_username] = round((t_logs[shot_name]['tasks'][task_type]['timelogs'][t_username] + float(t_dur)),3)
            else:
                t_logs[shot_name]['tasks'][task_type]['timelogs'][t_username] = float(t_dur)


        ttt = merge_two_dicts(t_logs, _t_logs)
        _t_logs = ttt

        progress+=progress_inc
        
        print("Progress: {}%".format(int(progress)))

    print 

    print  '{0}/{1} tasks processed'.format(num, len(task_ids))
        

users = list(set(users))

tasks_list = list(set(tasks_list))

create_sheet(out_file, _t_logs, users, tasks_list)

print 'File:',file
