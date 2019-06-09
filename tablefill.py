# -*- coding: utf-8 -*-
"""

@author: 枫林白鹭
"""

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
            
def Write_Result_Dict(result_dict,write_result_dict_tofile,json_path):          #写表结构到文件
    if(not write_result_dict_tofile):
        return
    else:
        with open(json_path,'w') as f_obj:
            json.dump(result_dict,f_obj)           



def Check_Completition_type(table_dict, cur):                    #检测完整性
    result = {}
#   result结构
#   result={ table_name: {
#                            '01数组（代表行填充形式）':相同形式数量
#                                    }
#}
    count = 0
    t = len(table_dict)
    for table in table_dict:
        if(table_dict[table]['row_num']>QUERY_ROW_LIMITATION):
            count +=1
            print(table+"表记录数为:",table_dict[table]['row_num']," 程序跳过，不计算")
            print(count,"/",t)
            continue
        result=Check_Table_Comp(table_dict,cur,table,result)          #检测表的完整性
        count +=1
        print(count,"/",t)
        Write_Result_Dict(result,write_result_dict_tofile,json_path2) #保存结果


def Check_Table_Comp(table_dict, cur, table_name,result):
    table_comp_result = result
    table_comp_result[table_name]={}
    sql = "select * from " + table_name           #组装sq语句
    print(sql)
    cur.execute(sql)
    for res in cur:
        a=np.array(res)
        a[a!=None]='1'
        a[a==None]='0'
        b=''.join('%s' %id for id in a)
        '''
        二进制代码参考
        print(a.shape)
        # 转换算子
        Bi_conver_op=2**np.arange(a.shape[0]) # shape=[1,6]
        print("Bi_conver_op",Bi_conver_op)
        
        b=a.dot(Bi_conver_op[::-1].T)
       
        print("b",bin(b)) 
        '''
        if b in table_comp_result[table_name]:
            table_comp_result[table_name][b]+=1
        else:
            table_comp_result[table_name][b]=1      
    print(table_comp_result)
    return  table_comp_result

QUERY_ROW_LIMITATION = 1000000  #多于该数值不查找具体空条目
read_table_dict_from_db = False                #是否从数据库读表结构，False为从文件读取，True为从数据库读
write_table_dict_tofile = False               #是否要将Table_Dict写入到文件
write_result_dict_tofile=True                #是否要将Result_Dict写入到文件
table_dict= {}                                  #建立表结构容器
json_path = "table_dict.json"
json_path2 = "result_dict.json"
link_word = 'C##SCYW/SCYW@219.216.69.63:1521/orcl'  #连接词
print("connecting to DB ...")
conn = cx_Oracle.connect(link_word)                                                #建立连接
cur = conn.cursor()
table_dict = Read_Table_Dict(read_table_dict_from_db,cur,json_path)       #读表结构
Write_Table_Dict(table_dict,write_table_dict_tofile,json_path)          #写表结构到文件
Check_Completition_type(table_dict, cur)
cur.close()



