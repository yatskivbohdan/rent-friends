from app import app, conn
from flask import render_template, redirect, url_for, request, flash


storage = {"id": 11,
           "username": "admin",
           "password": "adminpass",
           "status": "client"}

@app.route('/')
def start():
    return redirect(url_for('login_page'))

################################################# Login
@app.route('/login')
def login_page():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        username, password, status = request.form.get('username'), request.form.get('pass'), request.form.get('status')
        (login, signup) = (True, False) if request.form.get('submit') == 'Log In' else (False, True)

        data = list(conn.execute('select id, username, password from "{}" where username=\'{}\''.format(status, username)))
        if login and len(data) and password==data[0][2]:
            (storage["id"], storage["username"], storage["password"]), storage["status"] = data[0], status
            return redirect(url_for('home_page'))

        elif signup and not len(data):
            storage["username"], storage["password"], storage["status"] = username, password, status
            return redirect(url_for('profile_page'))

    return redirect(url_for('login_page'))

################################################# Profile
@app.route('/profile')
def profile_page():
    return render_template('profile.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():

    storage["id"] = list(
        conn.execute('select max(id) from "{}"'.format(storage["status"])))[0][0] + 1
    query = 'insert into "{}" values ({}, \'{}\', {}, \'{}\', 200, '.format(
        storage["status"] ,storage["id"], request.form.get('full_name'), request.form.get('age'), request.form.get('phone')
    )
    if storage["status"] == 'friend':
        query += 'true, '
    query += '\'{}\', \'{}\');'.format(
        storage["username"], storage["password"]
    )
    conn.execute(query)


    return redirect(url_for('home_page'))

################################################# Home
@app.route('/home')
def home_page():
    if storage["status"] == 'client':
        nav = ['Rent friends', 'Send gift', 'Complaint', 'Deposit money', 'Pay bill', 'Requests']
    else:
        nav = ['Take a day off', 'Return gift', 'Withdraw money', 'Requests']
    return render_template('main.html', buttons=nav)


@app.route('/home', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        link = request.form.get('button')
        switcher = {
            'Rent friends': 'rent_page',
            'Send gift': 'gift_page',
            'Complaint': 'complaint_page',
            'Take a day off': 'dayoff_page',
            'Return gift': 'return_page',
            'Deposit money': 'deposit_page',
            'Withdraw money': 'withdraw_page',
            'Pay bill': 'bill_page',
            'Requests': 'requests_page'
        }
        return redirect(url_for(switcher[link]))

    return redirect(url_for('home_page'))


################################################# Rent
@app.route('/rent')
def rent_page():
    friends = list(conn.execute(
        'select id, full_name, age, phone_number from "friend" where available=true'
    ))
    friends = list((x[0], "   ".join(map(str, x[1:]))) for x in friends)

    locations = list(conn.execute('select * from "locations"'))
    locations = list((x[0], x[2] + " - " + ", ".join(map(str, (x[1], ) + x[3:]))) for x in locations)

    return render_template('rent.html', friends=friends, locations=locations)


@app.route('/rent', methods=['GET', 'POST'])
def rent():
    if request.method == 'POST':
        friends_id = request.form.getlist('friend')
        location_id = request.form.get('locs')
        date = request.form.get('date')

        # celebration
        number_of_friends = len(friends_id)
        celebration_type = "date" if number_of_friends == 1 else "party"
        conn.execute('insert into "celebration" values (default, \'{}\', {}, default);'.format(
            celebration_type, number_of_friends))
        celebration_id = list(conn.execute('select max(id) from "celebration"'))[0][0]

        # order
        conn.execute('insert into "orders" values (default, {}, {}, \'{}\', {});'.format(
            storage["id"], location_id, date, celebration_id))
        order_id = list(conn.execute('select max(id) from "orders"'))[0][0]

        # payment
        conn.execute('insert into "payment" values (default, {}, {}, false);'.format(
            order_id, number_of_friends * 50))

        # order_friends
        for friend_id in friends_id:
            conn.execute('insert into "order_friends" values (default, {}, {});'.format(
                order_id, friend_id))

        return redirect(url_for('home_page'))

    return redirect(url_for("rent_page"))


################################################# Gift
@app.route('/sendgift')
def gift_page():
    friends = list(conn.execute(
        'select id, full_name, age, phone_number from "friend"'
    ))
    friends = list((x[0], "   ".join(map(str, x[1:]))) for x in friends)

    return render_template('sendgift.html', friends=friends)


@app.route('/sendgift', methods=['GET', 'POST'])
def gift():
    if request.method == 'POST':
        friend_id = request.form.get('friend')
        gift_name = request.form.get('gift')
        date = request.form.get('date')
        query = 'insert into "present" values (default, \'{}\', {}, \'{}\', false, \'{}\');'.format(
            gift_name, storage["id"], friend_id, date)
        conn.execute(query)

        return redirect(url_for('home_page'))

    return redirect(url_for("gift_page"))


################################################# Complaint
@app.route('/complaint')
def complaint_page():
    query = """select friend.id, full_name from "friend" 
                join order_friends on friend.id=friend_id 
                join orders on order_id=orders.id 
                where client_id={};""".format(storage["id"])
    friends = list(conn.execute(query))

    query = """select orders.id, locations.name, order_date from orders
                join locations on location_id=locations.id
                where client_id={};""".format(storage["id"])
    orders = list(conn.execute(query))
    orders = [(x[0], '{}   {}'.format(x[1], x[2])) for x in orders]

    return render_template('complaint.html', friends=friends, orders=orders)


@app.route('/complaint', methods=['GET', 'POST'])
def complaint():
    if request.method == 'POST':
        friend_id = request.form.get('friends')
        order_id = request.form.get('orders')
        date = request.form.get('date')
        message = request.form.get('message')
        coincide = len(list(conn.execute('select * from order_friends where order_id={} and friend_id={}'.format(
            order_id, friend_id))))
        if coincide:
            query = 'insert into complaints values (default, {}, {}, \'{}\', \'{}\');'.format(
                friend_id, order_id, date, message)
            conn.execute(query)

            return redirect(url_for('home_page'))

    return redirect(url_for("complaint_page"))


################################################# Day Off
@app.route('/dayoff')
def dayoff_page():
    return render_template('dayoff.html')


@app.route('/dayoff', methods=['GET', 'POST'])
def dayoff():
    if request.method == 'POST':
        date = request.form.get('date')
        message = request.form.get('message')
        conn.execute('insert into days_off values (default, {}, \'{}\', \'{}\');'.format(storage["id"], date, message))

        return redirect(url_for('home_page'))

    return redirect(url_for("dayoff_page"))


################################################# Return Gift
@app.route('/return')
def return_page():
    gifts = list(conn.execute('select id, name from present where friend_id={} and returned=false;'.format(
        storage["id"])))
    return render_template('return.html', gifts=gifts)


@app.route('/return', methods=['GET', 'POST'])
def return_gift():
    if request.method == 'POST':
        gift_id = request.form.get('gifts')
        conn.execute('update present set returned=true where id={};'.format(gift_id))

        return redirect(url_for('home_page'))

    return redirect(url_for("return_page"))


################################################# Deposit Money
@app.route('/deposit')
def deposit_page():
    return render_template('deposit.html',)


@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if request.method == 'POST':
        money = request.form.get('deposit')
        balance = list(conn.execute('select cash from {} where id={}'.format(storage["status"], storage["id"])))[0][0]
        balance = int(balance) + int(money)
        conn.execute('update {} set cash={} where id={};'.format(storage["status"], balance, storage["id"]))

        return redirect(url_for('home_page'))

    return redirect(url_for("deposit_page"))


################################################# Withdraw Money
@app.route('/withdraw')
def withdraw_page():
    return render_template('withdraw.html',)


@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if request.method == 'POST':
        money = request.form.get('withdraw')
        balance = list(conn.execute('select cash from {} where id={}'.format(storage["status"], storage["id"])))[0][0]
        if int(balance) >= int(money):
            balance = int(balance) - int(money)
            conn.execute('update {} set cash={} where id={};'.format(storage["status"], balance, storage["id"]))

            return redirect(url_for('home_page'))

    return redirect(url_for("withdraw_page"))


################################################# Pay bill
@app.route('/bill')
def bill_page():
    bills = list(conn.execute("""select payment.id, total_sum from payment
                                    join orders on order_id = orders.id
                                    where client_id={} and payed=False""".format(storage["id"])))
    return render_template('bill.html', bills=bills)


@app.route('/bill', methods=['GET', 'POST'])
def bill():
    if request.method == 'POST':
        bill_id = request.form.get('bills')
        query = 'select total_sum from payment where id={}'.format(bill_id)
        cost = int(list(conn.execute(query))[0][0])

        balance = list(conn.execute('select cash from {} where id={}'.format(storage["status"], storage["id"])))[0][0]
        if int(balance) >= int(cost):
            balance = int(balance) - int(cost)
            conn.execute('update {} set cash={} where id={};'.format(storage["status"], balance, storage["id"]))
            conn.execute('update payment set payed=true where id={};'.format(bill_id))

            return redirect(url_for('home_page'))

    return redirect(url_for("bill_page"))


################################################# Requests
@app.route('/requests')
def requests_page():
    req_list = [
        'для клiєнта C знайти усіх друзів, яких він наймав принаймні N разів за вказаний період (з дати F по дату T)',
        'для найманого друга Х знайти усіх клієнтів, які наймали його принаймні N разів за вказаний період (з дати F по дату T)',
        'для найманого друга Х знайти усі свята, на які його наймали принаймні N разів за вказаний період (з дати F по дату T)',
        'знайти усіх клієнтів, які наймали щонайменше N різних друзів за вказаний період (з дати F по дату T)',
        'знайти усіх найманих друзів, яких наймали хоча б N разів за вказаний період (з дати F по дату T)',
        'знайти сумарну кiлькiсть побачень по мiсяцях',
        'для найманого друга Х та кожного свята, на якому він побував, знайти скільки разів за вказаний період (з дати F по дату T) він був найнятий на свято у групі з принаймнi N друзів',
        'вивести подарунки у порядку спадання середньої кількостi вихідних, що брали наймані друзі, які отримували подарунок від клієнта С протягом вказаного періоду (з дати F по дату T)',
        'вивести найманих друзів у порядку спадання кількость скарг від груп з принаймні N клієнтів за вказаний період (з дати F по дату T)',
        'знайти усі спільні події для клієнта С та найманого друга Х за вказаний період (з дати F по дату T)',
        'знайти усі днi коли вихідними були від А до В найманих друзів, включно',
        'по місяцях знайти середню кількість клієнтів у групі, що реєстрували скаргу на найманого друга Х',
    ]
    return render_template('requests.html', req_list=req_list)


@app.route('/requests', methods=['GET', 'POST'])
def requests():
    if request.method == 'POST':
        req = int(request.form.get('reqs'))
        C = request.form.get('C')
        X = request.form.get('X')
        N = request.form.get('N')
        F = request.form.get('F')
        T = request.form.get('T')
        A = request.form.get('A')
        B = request.form.get('B')

        query = ''
        title = []
        if req == 0 and C and F and T:
            query = """select friend.full_name from friend
                        inner join order_friends on friend.id = order_friends.friend_id
                        inner join orders on order_friends.order_id = orders.id
                        inner join client on orders.client_id = client.id
                        where orders.order_date BETWEEN '{}' AND '{}'
                        and client.full_name = '{}' 
                        group by friend.full_name
                        having count(friend.full_name)>={}""".format(F, T, C, N)
        elif req == 1 and X and F and T:
            query = """SELECT client.full_name
                        FROM client JOIN orders on client.id = orders.client_id
                        JOIN order_friends on order_friends.order_id = orders.id
                        JOIN friend on friend.id = order_friends.friend_id
                        WHERE orders.order_date BETWEEN '{}' AND '{}'
                        AND friend.full_name = '{}'
                        GROUP BY client.full_name
                        HAVING COUNT(friend.id)>={};""".format(F, T, X, N)
        elif req == 2 and X and F and T:
            query = """SELECT locations.name, orders.order_date
                        FROM orders JOIN order_friends on orders.id = order_friends.order_id
                        JOIN friend on friend.id = order_friends.friend_id
                        JOIN locations on locations.id = orders.location_id
                        WHERE orders.order_date BETWEEN '{}' AND '{}'
                        AND friend.full_name = '{}'
                        GROUP BY locations.name, orders.order_date
                        HAVING COUNT(friend.id)>={};""".format(F, T, X, N)
            title = ('Location', 'Date')
        elif req == 3 and F and T:
            query = """SELECT client.full_name
                        FROM client JOIN orders on client.id = orders.client_id
                        JOIN order_friends on order_friends.order_id = orders.id
                        JOIN friend on friend.id = order_friends.friend_id
                        WHERE orders.order_date BETWEEN '{}' AND '{}'
                        GROUP BY client.full_name
                        HAVING COUNT(DISTINCT friend.id)>={};""".format(F, T, N)
        elif req == 4 and F and T:
            query = """SELECT friend.full_name
                        FROM client JOIN orders on client.id = orders.id
                        JOIN order_friends on order_friends.order_id = orders.id
                        JOIN friend on friend.id = order_friends.friend_id
                        WHERE orders.order_date BETWEEN '{}' AND '{}'
                        GROUP BY friend.full_name
                        HAVING COUNT(friend.id)>={};""".format(F, T, N)
        elif req == 5:
            query = """SELECT EXTRACT(month FROM(Orders.order_date)), COUNT(EXTRACT(month FROM(Orders.order_date)))
                        FROM Celebration JOIN Orders on Celebration.id = Orders.celebration_id
                        WHERE Celebration.type ILIKE 'date'
                        GROUP BY EXTRACT(month FROM(Orders.order_date));"""
            title = ('Month', 'Count')
        elif req == 6 and X and F and T:
            query = """select count(*) from order_friends
                        inner join friend on order_friends.friend_id = friend.id
                        inner join orders on orders.id = order_friends.order_id
                        inner join celebration on orders.celebration_id=celebration.id
                        where friend.full_name = '{}'
                        and orders.order_date BETWEEN '{}' AND '{}'
                        and celebration.type = 'party' and celebration.number_of_friends >= {}""".format(X, F, T, N)
        elif req == 7 and C and F and T:
            query = """SELECT Present.name
                        FROM Present JOIN Friend on Friend.id = Present.friend_id
                        LEFT OUTER JOIN Days_off on Days_off.friend_id = Friend.id
                        JOIN client on Present.client_id=client.id
                        WHERE Present.present_date BETWEEN '{}' AND '{}'
                        AND client.full_name = '{}'
                        GROUP BY Present.name, Present.id
                        ORDER BY COUNT(Friend.id) DESC;""".format(F, T, C)
        elif req == 8 and F and T:
            query = """SELECT Friend.full_name
                        FROM Friend JOIN Complaints on Friend.id = Complaints.friend_id
                        JOIN client_group on client_group.complaint_id = Complaints.id
                        WHERE Complaints.date_of_complaints BETWEEN '{}' AND '{}'
                        GROUP BY Friend.id, Friend.full_name
                        HAVING COUNT(distinct client_group.client_id)>={}
                        ORDER BY COUNT(distinct Complaints.id) DESC, COUNT(distinct client_group.client_id)""".format(F, T, N)
        elif req == 9 and F and T and C and X:
            query = """SELECT locations.name, orders.order_date
                        FROM Orders JOIN Client on Client.id = Orders.client_id
                        JOIN order_friends on order_friends.order_id = Orders.id
                        JOIN Friend on Friend.id = order_friends.friend_id
                        JOIN locations on locations.id = orders.location_id
                        WHERE Orders.order_date BETWEEN '{}' AND '{}'
                        AND Friend.full_name = '{}'
                        AND Client.full_name = '{}'
                        GROUP BY locations.name, orders.order_date""".format(F, T, X, C)
            title = ('Order ID',)
        elif req == 10:
            query = """select date_of_rest from days_off
                        group by date_of_rest
                        having count(date_of_rest)>= {} and count(date_of_rest)<={}""".format(A, B)
        elif req == 11 and X:
            query = """SELECT EXTRACT(month FROM(Complaints.date_of_complaints)), 
                        CAST(COUNT(client_group.client_id) AS FLOAT) / CAST(COUNT(distinct Complaints.id) AS FLOAT)
                        FROM Complaints JOIN client_group on Complaints.id = client_group.complaint_id
                        join friend on complaints.friend_id = friend.id
                        WHERE friend.full_name = '{}'
                        GROUP BY EXTRACT(month FROM(Complaints.date_of_complaints));""".format(X)
            title = ('Month', 'Average')

        if query:
            result = list(conn.execute(query))
            if req == 5 or req == 11:
                result = [(int(r[0]), r[1]) for r in result]
            if title: result = [title] + result
            result = ['   ,   '.join(map(str, x)) for x in result]
            return render_template("result.html", result=result)


    return redirect(url_for("requests_page"))