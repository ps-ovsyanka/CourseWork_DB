
from datetime import datetime
from flask import Flask, render_template, request, redirect, session
import psycopg2

app = Flask(__name__)
app.secret_key = 'app secret key'


@app.route('/')
def base():
    return redirect("/catalog")



@app.route('/catalog')
def show_catalog():
    con = connection()
    cursor=con.cursor()
    cursor.execute("select * from all_catalog;")
    result = cursor.fetchall()
    return render_template('catalog.html', result=result)

@app.route('/critical_norm_list')
def critical_norm_list():
    con = connection()
    cursor=con.cursor()
    cursor.execute("select * from critical_norm_list;")
    result = cursor.fetchall()
    return render_template('critical_norm_list.html', result=result)


@app.route('/min_stock', methods = ['GET','POST'])
def min_stock():
    con = connection()
    cursor=con.cursor()
    if request.method == 'POST':
        if request.form['type'] == 'Не указано':
            cursor.execute("select name, type, in_stock from medicament where in_stock = (select MIN(in_stock) from medicament);")
        else:
            cursor.execute(f"select name, type, in_stock from medicament where in_stock = (select MIN(in_stock) from medicament where type='{request.form['type']}') and type='{request.form['type']}';") 
    else:
        cursor.execute("select name, type, in_stock from medicament where in_stock = (select MIN(in_stock) from medicament);")

    result = cursor.fetchall()
    cursor.execute("select name from type;")
    res_type = cursor.fetchall()
    return render_template('min_stock.html', res_type=res_type, result=result)


@app.route('/add_medicament', methods = ['GET','POST'])
def add_medicament():
    con = connection()
    cursor=con.cursor()
    if request.method == 'POST':
        res = request.form
        cursor.execute("Call add_medicament('"+res['med']+"','"+res['type']+"',"+res['price']+"," +res['norm']+",'"+res['life_1'] + " " +res['life_2']+"')")
        con.commit()
        return redirect("/catalog")
    else :
        cursor.execute("select name from type")
        result = cursor.fetchall()
        return render_template('add_medicament.html', result=result)
        

@app.route('/medicament_info', methods = ['GET','POST'])
def show_medicament_info():
    con = connection()
    cursor=con.cursor()
    med = request.args.get('id')
    print(med)
    result2 = []
    result3 = []
    cursor.execute(f"select name, type, price, in_stock from medicament where name='{med}';")
    result1 = cursor.fetchall()
    cursor.execute(f"select count(medicament) from technology where medicament='{med}';")
    techn = cursor.fetchone()
    print(techn[0])
    if ( int(techn[0]) > 0):
        cursor.execute(f"select method, ready_time from technology where medicament='{med}';")
        result2 = cursor.fetchall()
        cursor.execute(f"select components_reference.medicament, medicament.price from (components_reference join medicament on (components_reference.medicament=medicament.name)) where components_reference.technology=(select id_technology from technology where medicament='{med}') ")
        result3 = cursor.fetchall()
    if request.method == 'POST':
        cursor.execute(f"delete from technology where medicament='{med}';")
        con.commit()
        return redirect('/catalog')
    return render_template('medicament_info.html', result1=result1, result2=result2, result3=result3)



@app.route('/technology', methods = ['GET','POST'])
def technology():
    con = connection()
    cursor=con.cursor()
    type_id=1
    cursor.execute(f"SELECT name FROM type")
    res_type = cursor.fetchall()
    cursor.execute(f"select distinct medicament, method, ready_time from technology;")
    result = cursor.fetchall()
    if request.method == 'POST' and request.form['type'] != 'Не указано':
        cursor.execute(f"select distinct medicament, method, ready_time from technology, medicament where technology.medicament=medicament.name and type ='{request.form['type']}' ;")
        result = cursor.fetchall()
        type_id = res_type.index((request.form['type'],)) + 2
    
    
    
    return render_template('technology.html', result=result, res_type=res_type, type= type_id)
    

@app.route('/add_tecnology', methods = ['GET','POST'])
def add_tecnology():
    con = connection()
    cursor=con.cursor()
    if request.method == 'POST': 
        if 'act' in request.form:
            if str(request.form['act']) == '+':
                cursor.execute("select name from medicament")
                result = cursor.fetchall()            
                return render_template('add_tecnology.html', result=result, count=(len(request.form)-5))
            elif str(request.form['act']) == '-':
                cursor.execute("select name from medicament")
                result = cursor.fetchall()            
                return render_template('add_tecnology.html', result=result, count=(len(request.form)-7))
        else:
            r_time = str(request.form['life_1']) + " " + request.form['life_2']
            components = []
            i = 0
            while ('comp_'+str(i) in request.form):
                components.append(request.form['comp_'+str(i)])
                i += 1
            str_comp = str(components).replace('[', '{').replace(']', '}').replace('\'', '\"')
            cursor.execute(f"call add_tecnology('{request.form['med']}','{request.form['techology']}','{str_comp}','{r_time}')")
            con.commit()
        return redirect("/catalog")
    else :
        cursor.execute("select name from medicament")
        result = cursor.fetchall()
        return render_template('add_tecnology.html', result=result, count=0)


@app.route('/requests')
def requests():
    con = connection()
    cursor=con.cursor()
    cursor.execute("select * from request")
    result = cursor.fetchall()
    return render_template('requests.html', result=result)


@app.route('/create_request', methods = ['GET','POST'])
def create_requests():
    con=connection()
    cursor = con.cursor()

    if request.method == 'POST':
        med=request.form['med']
        count=request.form['count']
        
        query=f"call create_request('{med}', {count});"
        cursor.execute(query)
        con.commit()
        return redirect("/requests")
    else:
        query="select name from medicament"
        cursor.execute(query)
        result2 = cursor.fetchall()
        return render_template('create_request.html', result=result2)


@app.route('/complete_request', methods = ['GET','POST'])
def complete_request():
    con=connection()
    cursor = con.cursor()

    if request.method == 'POST':         
        for ch in request.form:
            cursor.execute(f"call accepted_request({request.form[ch]});")
            con.commit()
        return redirect("/requests")
    else:
        query="SELECT row_number() over () as number, * FROM request where date_completed is NULL;"
        cursor.execute(query)
        result = cursor.fetchall()
        return render_template('complete_request.html', result=result)

    

@app.route('/orders', methods = ['GET','POST'])
def orders():
    con = connection()
    cursor=con.cursor()
    cursor.execute('call upd_orders()')
    con.commit()
    stat=1
    if(request.method == 'POST' and request.form['status'] != 'Не указано'):
        cursor.execute(f"SELECT \"order\".id_order,recipe.medicament,recipe.count,customer.name,\"order\".registration_time,\"order\".ready_time,\"order\".status FROM \"order\",recipe,customer WHERE recipe.id_recipe = \"order\".recipe AND recipe.customer = customer.id_customer and status='{request.form['status']}'")
        if request.form['status'] == 'В производстве':
            stat = 2 
        elif request.form['status'] == 'Нет на складе':
            stat = 3
    else:
        cursor.execute('SELECT "order".id_order,recipe.medicament,recipe.count,customer.name,"order".registration_time,"order".ready_time,"order".status FROM "order",recipe,customer WHERE recipe.id_recipe = "order".recipe AND recipe.customer = customer.id_customer')
    result = cursor.fetchall()
    return render_template('orders.html', result=result, amount=len(result), status=stat)


@app.route('/add_order', methods = ['GET','POST'])
def add_order():
    name = ""
    amount = ""
    name_doctor = ""
    diagnos = ""
    msg=""
    msg_req=""
    con = connection()
    cursor=con.cursor()
    if request.method == 'POST':
        cursor.execute(f"select name from medicament where name='{request.form['name']}'")
        result = cursor.fetchone()
      
        if str(result) != "[]" :

            id_cust = -1  #поиск покупателя в списке
            cursor.execute(f"select customer.id_customer from customer where name='{request.form['name']}'")
            id_cust_result = cursor.fetchone()
            if (id_cust_result != None):#получение его id
                print(id_cust_result)
                id_cust = id_cust_result[0]
            else:#добавление нового покупателя
                q = f"call add_customer('{request.form['name']}');"
                print(q)
                cursor.execute(q)
                con.commit()
                cursor.execute(f"SELECT customer.id_customer FROM customer ORDER BY id_customer DESC LIMIT 1")
                result = cursor.fetchone()
                id_cust = result[0]

            cursor.execute(f"select count(medicament) from stock where medicament = '{request.form['med']}' GROUP BY medicament")
            result = cursor.fetchone()
            b = int(result[0]) if result != None else 0
            if (b >= int(request.form['amount'])):#проверка на наличие медикаментов            
                q = f"call register_order('{str(request.form['med'])}',{request.form['amount']},{id_cust},'{request.form['name_doctor']}','{request.form['diagnos']}', 'Готов');"
                cursor.execute(q)
                con.commit()    
                return redirect("/orders")

            elif request.form['phone'] != "":
                #Обновление адреса и телефона
                cursor.execute(f"UPDATE customer SET number_phone='{request.form['phone']}', address='{request.form['adres']}'  where id_customer={id_cust};")
                con.commit()
                
                cursor.execute(f"select id_technology from technology where medicament='{request.form['med']}'")
                components = cursor.fetchone()
                if  components == None :#Если нет технологии
                    q = f"call register_order('{str(request.form['med'])}',{request.form['amount']},{id_cust},'{request.form['name_doctor']}','{request.form['diagnos']}', 'Нет на складе');"
                    print(q)
                    cursor.execute(q)
                    con.commit()
                else :
                    cursor.execute(f"select medicament from components_reference where technology='{components[0]}'")
                    print('techno'+ str(components[0]))
                    components = cursor.fetchall()
                    flag = True
                    for value in components:
                        cursor.execute(f"select medicament from stock where medicament='{value[0]}'")
                        result = cursor.fetchone()
                        flag = False if result == None else True
                        
                    if flag :#Если есть все компоненты
                        for value in components:
                            cursor.execute(f"select id_medicament from stock where medicament='{value[0]}'")
                            id_med_del = (cursor.fetchone())[0]
                            cursor.execute(f"delete from stock where id_medicament={id_med_del}")
                            con.commit()
                        q = f"call register_order('{str(request.form['med'])}',{request.form['amount']},{id_cust},'{request.form['name_doctor']}','{request.form['diagnos']}', 'В производстве');"
                        print(q)
                        cursor.execute(q)
                        con.commit()
                    else:
                        q = f"call register_order('{str(request.form['med'])}',{request.form['amount']},{id_cust},'{request.form['name_doctor']}','{request.form['diagnos']}', 'Нет на складе');"
                        print(q)
                        cursor.execute(q)
                        con.commit()                

            else:
                name = request.form['name']
                amount = request.form['amount']
                name_doctor = request.form['name_doctor']
                diagnos = request.form['diagnos']
                msg="Не все медикаменты есть на складе. Заполните дополнительные данные"
                msg_req="required"
        else:
            msg=""
        return redirect ("/orders")
    cursor.execute("select name from medicament")
    result = cursor.fetchall()
    return render_template('add_order.html', result=result, msg=msg, msg_req=msg_req, name=name,amount=amount,name_doctor=name_doctor,diagnos=diagnos)



@app.route('/accept_order', methods = ['GET','POST'])
def accept_order():
    con = connection()
    cursor=con.cursor()
    cursor.execute(f"update \"order\" set status='Выдан' where id_order={request.args.get('id')}")
    con.commit()
    return redirect('/orders')



@app.route('/missing_components', methods = ['GET','POST'])
def missing_components():
    con = connection()
    cursor=con.cursor()
    cursor.execute('SELECT id_order, medicament, "count" FROM missing_components')
    result = cursor.fetchall()
    return render_template('missing_components.html', result=result, amount=len(result))



@app.route('/customers', methods = ['GET','POST'])
def customers():
    con = connection()
    cursor=con.cursor()
    stat=1
    if(request.method == 'POST' and request.form['status'] != 'Не указано' and request.form['type'] != 'Не указано'):
        cursor.execute(f"SELECT DISTINCT customer.name, number_phone, address FROM customer, \"order\", recipe, medicament WHERE status='{request.form['status']}' and recipe.customer=id_customer and recipe=id_recipe and type = '{request.form['type']}' and medicament.name = recipe.medicament")
        
        if request.form['status'] == 'Готов':
            stat = 2 
        elif request.form['status'] == 'Нет на складе':
            stat = 3
    elif (request.method == 'POST' and request.form['status'] == 'Не указано' and request.form['type'] != 'Не указано'):
        cursor.execute(f"SELECT DISTINCT customer.name, number_phone, address FROM customer, \"order\", recipe, medicament WHERE recipe.customer=id_customer and recipe=id_recipe and type = '{request.form['type']}' and medicament.name = recipe.medicament")
    elif (request.method == 'POST' and request.form['status'] != 'Не указано' and request.form['type'] == 'Не указано'):
        cursor.execute(f"SELECT DISTINCT customer.name, number_phone, address FROM customer, \"order\", recipe WHERE status='{request.form['status']}' and recipe.customer=id_customer and recipe=id_recipe")
        if request.form['status'] == 'Готов':
            stat = 2 
        elif request.form['status'] == 'Нет на складе':
            stat = 3
    else:
        cursor.execute(f"SELECT customer.name, number_phone, address FROM customer")
    result = cursor.fetchall()
    cursor.execute(f"SELECT name FROM type")
    res_type = cursor.fetchall()
    return render_template('customers.html', result=result, amount=len(result), res_type=res_type, status=stat)


@app.route('/periods_customers', methods = ['GET','POST'])
def periods_customers():
    con = connection()
    cursor=con.cursor()
    cursor.execute(f"SELECT name FROM type")
    res_type = cursor.fetchall()
    period_id=1
    type_id=1
    cursor.execute(f"SELECT DISTINCT customer.name, number_phone, address FROM customer")
    result = cursor.fetchall()
    if(request.method == 'POST' and request.form['period'] == 'Все время'):
        if (request.form['type'] == 'Не указано'):
            cursor.execute(f"SELECT DISTINCT customer.name, number_phone, address FROM customer")
            result = cursor.fetchall()
        else:
            cursor.execute(f"SELECT DISTINCT customer.name, number_phone, address FROM customer, \"order\", recipe, medicament where type='{request.form['type']}' and id_recipe=recipe and id_customer=customer and medicament.name=recipe.medicament")
            result = cursor.fetchall()
            type_id = res_type.index((request.form['type'],)) + 2

    elif(request.method == 'POST' and request.form['period'] == 'Неделя'):
        if (request.form['type'] == 'Не указано'):
            cursor.execute(f"SELECT DISTINCT customer.name, number_phone, address FROM customer where \"order\".registration_time > (CURRENT_TIMESTAMP - interval  '7 days')")
            result = cursor.fetchall()
        else:
            cursor.execute(f"SELECT DISTINCT customer.name, number_phone, address FROM customer, \"order\", recipe, medicament where type='{request.form['type']}' and id_recipe=recipe and id_customer=customer and medicament.name=recipe.medicament and \"order\".registration_time > (CURRENT_TIMESTAMP - interval  '7 days')")
            result = cursor.fetchall()
            type_id = res_type.index((request.form['type'],)) + 2
        period_id=2

    elif(request.method == 'POST' and request.form['period'] == 'Месяц'):
        if (request.form['type'] == 'Не указано'):
            cursor.execute(f"SELECT DISTINCT customer.name, number_phone, address FROM customer where \"order\".registration_time > (CURRENT_TIMESTAMP - interval  '1 month')")
            result = cursor.fetchall()
        else:
            cursor.execute(f"SELECT DISTINCT customer.name, number_phone, address FROM customer, \"order\", recipe, medicament where type='{request.form['type']}' and id_recipe=recipe and id_customer=customer and medicament.name=recipe.medicament and \"order\".registration_time > (CURRENT_TIMESTAMP - interval  '1 month')")
            result = cursor.fetchall()
            type_id = res_type.index((request.form['type'],)) + 2
        period_id=3


    
    return render_template('periods_customers.html', result=result, amount=len(result), res_type=res_type, period=period_id, type=type_id)


@app.route('/regular_customers')
def regular_customers():
    con = connection()
    cursor=con.cursor()
    
    cursor.execute(f"SELECT customer.name, count(name) as orders FROM customer, \"order\", recipe where recipe=id_recipe and customer=id_customer group by name order by orders desc LIMIT 10 ")
    result = cursor.fetchall()
    return render_template('regular_customers.html', result=result)

@app.route('/regular_medicament', methods = ['GET','POST'])
def regular_medicament():
    con = connection()
    cursor=con.cursor()
    cursor.execute(f"SELECT name, count(name) as count  FROM medicament, \"order\", recipe where recipe=id_recipe and medicament=name group by name order by count desc LIMIT 10 ")
    result = cursor.fetchall()
    cursor.execute(f"select name from type")
    res_type = cursor.fetchall()
    if request.method == 'POST':
        cursor.execute(f"SELECT name, count(name) as count  FROM medicament, \"order\", recipe where recipe=id_recipe and  medicament=name and type='{request.form['type']}' group by name order by count desc LIMIT 10 ")
        result = cursor.fetchall()
    return render_template('regular_medicament.html', result=result, res_type=res_type)

def connection():
    conn = psycopg2.connect(dbname='Pharmacy', user='postgres', 
                        password='Kraterept', host='localhost')
    return conn



if __name__ == "__main__":
    
    app.run(debug=True)