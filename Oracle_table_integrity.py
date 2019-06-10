import os
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'
import cx_Oracle
import numpy as np
import json
import xlwt
#Table_Dict结构
# table_dict = {
    #table_name: {col_num:
    #              row_num:
    #              cols:{
#                        col_name:{
#                                data_type:
#                                distinct_num:
#                                nulls_num:
#                        }
    #              }
#} #

def Read_Table_Dict(from_db_flag, cur, json_path):
    table_dict = {}
    if(from_db_flag):                           #从数据库读
        print("read table dictionary from db")
        res = Read_All_Table_Names_From_DB(cur)                     #读Table信息
        for item in res:
            table_dict[item[0]] = {}
            table_dict[item[0]]['row_num'] = int(item[1])
            table_dict[item[0]]['col_num'] = 0
            table_dict[item[0]]['cols'] = {}
        print(len(table_dict), "tables has been read")

        res = Read_All_Col_From_DB(cur)                                     #读Column信息
        for item in res:
            table_name = item[0]
            table_dict[table_name]['col_num'] += 1
            table_dict[table_name]['cols'][item[1]] = {}
            table_dict[table_name]['cols'][item[1]]['data_type'] = item[2]
            table_dict[table_name]['cols'][item[1]]['distinct_num'] = item[3]
            table_dict[table_name]['cols'][item[1]]['nulls_num'] = item[4]
        print(len(res), "columns has been read")

    else:                                                                                       #从json文件读信息
        print("read table dictionary from json")
        with open(json_path, 'rb') as f_obj:
            table_dict = json.load(f_obj)
        col_num = 0
        for table in table_dict:
            col_num =   table_dict[table]['col_num'] + col_num
        print("table dictionary has been read, there are ",len(table_dict), " tables and ", col_num, " columns in it")
    return table_dict
def Read_All_Table_Names_From_DB(cur):
    sql = "select table_name, Num_rows from user_tables"
    cur.execute(sql)
    res = np.array(cur.fetchall())
    return res
def Read_All_Col_From_DB(cur):
    cols = ["table_name,",
            "column_name,",
            "data_type,",
            "num_distinct,",
            "num_nulls"]
    sql = "select "
    for col_name in cols:
        sql = sql + col_name
    sql = sql + " from user_tab_columns"
    cur.execute(sql)
    res = np.array(cur.fetchall())
    return res
def Write_Table_Dict(table_dict,write_table_dict_tofile,json_path):          #写表结构到文件
    if(not write_table_dict_tofile):
        return
    else:
        with open(json_path,'w') as f_obj:
            json.dump(table_dict,f_obj)



def Check_Completition(table_dict, cur):                    #检测完整性
    result = {}
    
    t = len(table_dict)
    count = 0
    wbk = xlwt.Workbook()
    sheet = wbk.add_sheet('Sheet1',cell_overwrite_ok=True) 
    for table in table_dict:
        result=Check_Table_Comp(table_dict,cur,table,result)          #检测表的完整性
        count +=1
        print(count,"/",t)
    sheet.write(0,0,'表名')
    sheet.write(0,1,'栅格数 行*列')
    sheet.write(0,2,'行数')
    sheet.write(0,3,'列数')
    sheet.write(0,4,'空列数')
    sheet.write(0,5,'满列数')
    sheet.write(0,6,'含空列数')
    sheet.write(0,7,'总非空值数')
    sheet.write(0,8,'非空值占比')
    sheet.write(0,9,'去空列行满度')
    sheet.write(0,10,'行填充度') 
    sheet.write(0,10,'列填充度')       
    col_num = 1
    for table_name in result:
            sheet.write(col_num,0,table_name)
            sheet.write(col_num,1,result[table_name]['total_grid_num'])
            sheet.write(col_num,2,result[table_name]['total_row_num'])
            sheet.write(col_num,3,result[table_name]['total_col_num'])
            sheet.write(col_num,4,result[table_name]['null_col_num'])
            sheet.write(col_num,5,result[table_name]['full_col_num'])
            sheet.write(col_num,6,result[table_name]['col_num_with_null_grid'])
            sheet.write(col_num,7,result[table_name]['not_null_grid'])
            sheet.write(col_num,8,result[table_name]['not_null_grid/total_grid_num'])
            sheet.write(col_num,9,result[table_name]['grid_comp_without_empty_cols'])
            sheet.write(col_num,10,result[table_name]['row_num_without_empty_cols'])
            sheet.write(col_num,10,result[table_name]['col_comp'])
            col_num = col_num+1
    wbk.save('表3.0.xls')     

def Check_Table_Comp(table_dict, cur, table_name,result):
    table_comp_result = result
    total_row_num = table_dict[table_name]['row_num']           #条目数
    total_col_num = table_dict[table_name]['col_num']               #列数
    total_grid_num = total_row_num * total_col_num                  #表中grid数量
    total_null_num = 0                                                  #null的grid数量
    null_col_num = 0                                                    #空列数
    col_num_with_null_grid = 0                                      #非全空或全满列数量
    full_col_num = 0                                                        #满列数量
    null_grid=0                                                      #空值数
    row_num_without_empty_cols=0                                       #非满行数                                          
    '''
    统计空值
    '''
    for col_name in table_dict[table_name]['cols']:
      if(table_dict[table_name]['cols'][col_name]['nulls_num']!=None):
         null_grid+=table_dict[table_name]['cols'][col_name]['nulls_num'] 
    
 
    col_name_with_null_list = []                                                      #非全空或全满列名容器
    col_name_list = []                                                                #非全满列名容器

    for c in table_dict[table_name]['cols']:
        if(table_dict[table_name]['cols'][c]['nulls_num'] == None):         #null_num没有数值
            null_col_num += 1
            continue
        total_null_num += table_dict[table_name]['cols'][c]['nulls_num']
        if(table_dict[table_name]['cols'][c]['nulls_num'] == total_row_num):    #如果全空
            null_col_num += 1
            col_name_list.append(c)
        elif(0<table_dict[table_name]['cols'][c]['nulls_num'] and table_dict[table_name]['cols'][c]['nulls_num'] < total_row_num):   #有空但不全空
            col_num_with_null_grid +=1
            col_name_with_null_list.append(c)
            col_name_list.append(c)
        else:                                                       #满列
            full_col_num +=1
    assert null_col_num + col_num_with_null_grid + full_col_num ==  total_col_num           #断言校验
    row_num_with_null_grid = 0                                              #有空项的条目数
    if(col_num_with_null_grid ==0 ):
        row_num_with_null_grid = 0
    elif(total_row_num > QUERY_ROW_LIMITATION):         #跳过大数据表，输出-1
        row_num_with_null_grid = -1
    else:                                                                                       #统计
        sql = "select count(1) from " + table_name +" where "           #组装sq语句
        while(len(col_name_with_null_list)>0):
            col_name = col_name_with_null_list.pop()
            sql = sql + col_name
            if(len(col_name_with_null_list)>0):
                sql = sql + " is null or "
            else:
                 sql = sql + " is null"
        print(sql)
        cur.execute(sql)
        row_num_with_null_grid = np.array(cur.fetchall())[0][0]
        
        if(null_col_num>0):
            row_num_without_empty_cols =total_row_num
        else:
            row_num_without_empty_cols = row_num_with_null_grid
    print(row_num_with_null_grid)
    table_comp_result[table_name]={}                                 #表名
    table_comp_result[table_name]['total_grid_num']=total_grid_num   #栅格数 行*列
    table_comp_result[table_name]['total_row_num']=total_row_num     #条目数（行数）
    table_comp_result[table_name]['total_col_num']=total_col_num    #列数
    table_comp_result[table_name]['null_col_num']=null_col_num      #空列数
    table_comp_result[table_name]['full_col_num']=full_col_num      #满列数 
    table_comp_result[table_name]['col_num_with_null_grid']=col_num_with_null_grid     #非全空且非全满列数量 
    table_comp_result[table_name]['not_null_grid']= total_grid_num-null_grid            #非空值数
    table_comp_result[table_name]['not_null_grid/total_grid_num']= (total_grid_num-null_grid)/total_grid_num if total_grid_num!=0 else 0            #非空值占比
    table_comp_result[table_name]['grid_comp_without_empty_cols']=1-(row_num_with_null_grid/total_row_num) if total_row_num!=0 else 0                   # 去空列行填充度
    table_comp_result[table_name]['row_num_without_empty_cols']=1-(row_num_without_empty_cols/total_row_num) if total_row_num!=0 else 0                 #整体行填充度
    table_comp_result[table_name]['col_comp']=full_col_num/total_col_num 
    return  table_comp_result

QUERY_ROW_LIMITATION = 10000000000   #多于该数值不查找具体空条目
read_table_dict_from_db = False                #是否从数据库读表结构，False为从文件读取，True为从数据库读
write_table_dict_tofile = False               #是否要将Table_Dict写入到文件
table_dict= {}                                  #建立表结构容器
json_path = "table_dict.json"
link_word = 'C##SCYW/SCYW@219.216.69.63:1521/orcl'  #连接词
print("connecting to DB ...")
conn = cx_Oracle.connect(link_word)                                                #建立连接
cur = conn.cursor()
table_dict = Read_Table_Dict(read_table_dict_from_db,cur,json_path)       #读表结构
Write_Table_Dict(table_dict,write_table_dict_tofile,json_path)          #写表结构到文件
Check_Completition(table_dict, cur)
cur.close()


