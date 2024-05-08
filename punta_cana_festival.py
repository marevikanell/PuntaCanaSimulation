import threading
import time
import random 
import concurrent.futures
import traceback
import datetime
import mysql.connector

# Person classes:

class Person:
    def __init__(self, id, age):
        self.id = id
        self.age = age

class Attendee(Person):
    def __init__(self, id, age, ticket, total_drinks, total_foods,total_treatments, total_bathroom_visits, total_stage_visits, gender, activities):
        super().__init__(id, age)
        self.is_inside = False
        self.ticket = ticket
        self.active = False
        
        self.entered_at = time.time()
        self.display_entered_at = datetime.datetime.now().time() # record times for sql
        self.display_exited_at = None
        
        # counters for sql connection 
        self.total_drinks = total_drinks
        self.total_foods = total_foods
        self.total_treatments = total_treatments
        self.total_bathroom_visits = total_bathroom_visits
        self.total_stage_visits = total_stage_visits
        
        self.activities = activities
        self.gender = gender
        
        self.has_free_ticket = random.choices([True, False], weights=[0.5, 0.5])[0]
        
        # base probabilities for bathroom and emergency
        self.needs_emergency = 0.001
        self.needs_bathroom = 0.1
    
    def pass_check(self, entrance):
        entrance.add_check(self)
        
    def decide_to_leave(self):
            time_spent = time.time() - self.entered_at # Time spent in hours
            base_probability = 0.0001  # Start with a very low base probability
            probability = base_probability + 0.005 * self.total_treatments + 0.002 * self.total_drinks + 0.001 * time_spent 
            
            if random.random() < probability:
                self.is_inside = False
                print(f"{self.id} is leaving the festival.")
                self.display_exited_at = datetime.datetime.now().time()

    def place_drink(self, menu_item, bar):
        try: 
            order = Order(self, menu_item, self.has_free_ticket)
            bar.add_order(order)
            self.total_drinks += 1
            return order
        except Exception as e:
            print(traceback.format_exc())
    
    def place_food(self, menu_item, food_truck):
        try:
            order = Order(self, menu_item, self.has_free_ticket)
            food_truck.add_order(order)
            self.total_foods += 1
            return order
        except Exception as e:
            print(traceback.format_exc())
            
    def go_to_stage(self, stage):
        try:
            stage_index = random.randint(0, len(stage.stages) - 1)
            artist = stage.get_current_performer(stage_index)
            stage_genre = stage.stages[stage_index]['genre']
            if artist:
                print(f"{self.id} is watching {artist.name} perform on {stage_genre} Stage")
                self.total_stage_visits += 1
            else:
                print(f"{self.id} went to {stage_genre} Stage, but there's no performance at the moment.")
                
            time.sleep(random.uniform(5.0, 10.0))
        except Exception as e:
            print(traceback.format_exc())
        
    def go_to_bathroom(self, bathroom):
        base_prob = self.needs_bathroom 
        incremental_increase = 0.1
        reduction_factor = 0.05
        prob = min(base_prob + incremental_increase * self.total_drinks - reduction_factor * self.total_bathroom_visits, 1.0)
        # realistic probability of needing the bathroom
        
        if random.random() < prob:
            print(f"{self.id} is going to the bathroom")
            bathroom.request_use(self)
            self.total_bathroom_visits += 1
    
    def go_to_emergency(self, emergency_truck):
        base_prob = self.needs_emergency  
        incremental_increase = 0.05
        reduction_factor = 0.05
        prob = min(base_prob + incremental_increase * self.total_drinks - reduction_factor * self.total_treatments, 1.0)
        # realistic probability of needing emergency help

        if random.random() < prob:
            print(f"{self.id} is going to the emergency truck")
            emergency_truck.admit_patient(self)
            self.total_treatments += 1
    
    # main function for the attendee - runs in the threadpool - activity loop:
    def do_activities(self, bar, food_truck, bathroom, emergency_truck, stage):
        try:
                while self.is_inside:
                    
                    self.decide_to_leave()  #check everytime before doing an activity
                    
                    if not self.is_inside:
                        break # break if person is not inside anymore
                    
                    activity = random.choice(self.activities)
                    time.sleep(random.uniform(0.5, 1.5)) 
                                        
                    if not self.active:
                        self.active = True # avoid multiple activities at the same time
                        
                        if activity == 'drinks' and 'drinks' in self.activities:
                            drink_item = random.choice(bar.menu.items)
                            print(f"{self.id} is placing an order for {drink_item.name}")
                            self.place_drink(drink_item, bar)
                            
                        elif activity == 'food' and 'food' in self.activities:
                            food_item = random.choice(food_truck.menu.items)
                            print(f"{self.id} is placing an order for {food_item.name}")
                            self.place_food(food_item, food_truck)
                        
                        elif activity == 'music' and 'music' in self.activities:
                            self.go_to_stage(stage)
                        
                        elif activity == 'bathroom' and 'bathroom' in self.activities:
                            self.go_to_bathroom(bathroom)
                        
                        elif activity == 'emergency' and 'emergency' in self.activities:
                            self.go_to_emergency(emergency_truck)
                 
                        time.sleep(random.uniform(2, 5))  
                        self.active = False
                        
        except Exception as e:
            print(traceback.format_exc())

    def receive_notification(self, message):
        print(f'{self.id}: {message}')   

# Security and Entrance: 

class SecurityStaff(threading.Thread):
    def __init__(self, name, entrance):
        super().__init__(name=name)
        self.entrance = entrance
    
    def run(self):
        while True:
            attendee = self.entrance.get_next_attendee() # get attendee from queue
            if attendee is None:
                break
            print(f"{self.name} is checking {attendee.id}")
            time.sleep(random.uniform(0.2, 1))  
            if attendee.ticket.type != "No ticket":
                attendee.is_inside = True
                attendee.receive_notification('You are now inside! Enjoy the festival!')
                attendee.entered_at = time.time()
                attendee.display_entered_at = datetime.datetime.now().time() 
            else:
                attendee.receive_notification('You are not allowed to enter the festival. You have no ticket:( sorry!')
                attendee.display_entered_at = None # never entered
 
class TicketType:
    def __init__(self, type):
        self.type = type
    def __str__(self):
        return f"Ticket Type: {self.type}"

class Entrance:
    def __init__(self, security_count):
        self.attendees = []
        self.securities = []
        self.lock = threading.Lock()
        for i in range(security_count):
            security = SecurityStaff(f'Security {i+1}', self)
            self.securities.append(security)

    def add_check(self, attendee):
        self.lock.acquire() # lock the queue while being used
        self.attendees.append(attendee)
        self.lock.release()

    def get_next_attendee(self):
        self.lock.acquire() # lock the queue while being processed by a security staff
        if self.attendees:
            attendee = self.attendees.pop(0)
            self.lock.release()
            return attendee
        self.lock.release()
        return None

    def start(self):
        for security in self.securities:
            security.start()
        for security in self.securities:
            security.join()
    

# Artist and Stage:

class Artist(threading.Thread):
    def __init__(self, name, genre, set_duration, stage, stage_index):
        super().__init__()
        self.name = name
        self.genre = genre
        self.set_duration = set_duration
        self.stage = stage  
        self.stage_index = stage_index # keep track for attendees to know which stage they can be watching
        self.currently_performing = False

    def run(self):
        stage_info = self.stage.stages[self.stage_index]
        stage_lock = stage_info['lock'] # get the lock for the stage from the dictionary
        stage_genre = stage_info['genre']

        with stage_lock:
            self.currently_performing = True
            self.stage.current_performers[self.stage_index] = self
            print(f"{self.name} starting their set of {self.set_duration} seconds on {stage_genre} Stage!")
            time.sleep(self.set_duration)
            print(f"{self.name} has finished their performance on {stage_genre} Stage!")
            self.currently_performing = False
            self.stage.current_performers[self.stage_index] = None

class Stage:
    def __init__(self, num_stages, artists_info):
        self.stages = [{'lock': threading.Lock(), 'genre': 'Pop'}, 
                       {'lock': threading.Lock(), 'genre': 'Rap'}, 
                       {'lock': threading.Lock(), 'genre': 'Reggaeton'}] # one lock for each genre stage 
        
        self.current_performers = [None] * num_stages  # Track who is performing at each stage
        self.artists = []
        for stage_index, stage_info in enumerate(self.stages):
            for artist_info in artists_info:
                if artist_info['genre'] == stage_info['genre']:
                    self.artists.append(Artist(
                        name=artist_info['name'],
                        genre=artist_info['genre'],
                        set_duration=artist_info['set_duration'],
                        stage=self,
                        stage_index=stage_index
                    ))

    def start_show(self):
        print("\n\nStage show starting!\n\n")
        for artist in self.artists:
            artist.start()
        for artist in self.artists:
            artist.join()
        print("\n\nStage show finished!\n\n PUNTA CANA WAS A BLAST! \n\n See you next year!\n\n") # signal to see it in the output

    def get_current_performer(self, stage_index):
        if stage_index < len(self.current_performers):
            artist = self.current_performers[stage_index]
            if artist and artist.currently_performing:
                return artist
        return None
    

# Bar and Food:

class Barista(threading.Thread):
    def __init__(self, name, bar):
        super().__init__(name=name)
        self.bar = bar
        self.order = None

    def run(self):
        try:
            while festival.festival_running:
                self.order = self.bar.get_next_order()
                if self.order is None:
                    continue # used to be a break condition, but now we keep the thread running until the festival ends
                else:           
                    self.order.status = 'in progress'
                    print(f"{self.name} is working on {self.order}") 
                    time.sleep(self.order.estimated_time)
                    self.order.status = 'completed'
                    festival.collect_order(self.order)
                    price_msg = 'free of charge!' if self.order.free_ticket else f'{self.order.menu_item.price}$ please.'
                    self.order.attendee.receive_notification(f'Your {self.order.menu_item.name} is ready. It will be {price_msg}')
        except Exception as e:
            print(traceback.format_exc())
    
class Cook(threading.Thread):
    def __init__(self, name, food_truck):
        super().__init__(name=name)
        self.food_truck = food_truck
        self.order = None

    def run(self):
        while festival.festival_running:
            self.order = self.food_truck.get_next_order()
            if self.order is None:
               continue
            self.order.status = 'in progress'
            print(f"{self.name} is working on {self.order}") 
            time.sleep(self.order.estimated_time)
            self.order.status = 'completed'
            festival.collect_order(self.order) # collect for the sql database 
            price_msg = 'free of charge!' if self.order.free_ticket else f'{self.order.menu_item.price}$ please.'
            self.order.attendee.receive_notification(f'Your {self.order.menu_item.name} is ready. It will be {price_msg}')

class MenuItem:
    def __init__(self, name, price, contains_alcohol, prep_time):
        self.name = name
        self.price = price
        self.contains_alcohol = contains_alcohol
        self.prep_time = prep_time
    
    
    def __str__(self) -> str:
        return f"{self.name} (Prep time: {self.prep_time}s, Price: ${self.price})"
        
class Menu_Bar:
    def __init__(self):
        self.items = [
            MenuItem('Soda', 3.50, False, 0.5),
            MenuItem('Water', 3, False, 0.5),
            MenuItem('Beer', 5.50, True, 0.8),
            MenuItem('Wine', 6, True, 0.9),
            MenuItem('Whiskey', 10, True, 1),
            MenuItem('Gin Tonic', 11, True, 2)
        ]
    
    def get_item_by_name(self, name):
        for item in self.items:
            if item.name == name:
                return item
        return None

class Menu_FoodTruck:
    def __init__(self):
        self.items = [
            MenuItem('Burger', 8, False, 1),
            MenuItem('Fries', 3.20 , False, 0.5),
            MenuItem('Hot Dog', 4.50, False, 0.8),
            MenuItem('Tacos', 4, False, 0.7),
            MenuItem('Wings', 3.60, False, 0.7),
            MenuItem('Wrap', 5, False, 0.5)
        ]
    
    def get_item_by_name(self, name):
        for item in self.items:
            if item.name == name:
                return item
        return None

class Order:
    def __init__(self, attendee, menu_item, free_ticket):
        self.attendee = attendee
        self.menu_item = menu_item
        self.status = 'waiting'
        self.estimated_time = menu_item.prep_time
        self.free_ticket = free_ticket

    def __str__(self):
        return f"{self.attendee.id}'s order: {self.menu_item} ({self.status})"
        
class Bar:
    def __init__(self, barista_count):
        self.menu = Menu_Bar()
        self.orders = []
        self.baristas = []
        self.orders_lock = threading.Lock()
        for i in range(barista_count):
            barista = Barista(f'Barista {i+1}', self)
            self.baristas.append(barista)

    def add_order(self, order):
        with self.orders_lock: 
            self.orders.append(order)

    def get_next_order(self):
        self.orders_lock.acquire()
        if len(self.orders) > 0:
            order = self.orders.pop(0)
            self.orders_lock.release()
            return order
        self.orders_lock.release()
        return None

    def start(self):
        for barista in self.baristas:
            barista.start()

        for barista in self.baristas:
            barista.join()

class FoodTruck:
    def __init__(self, cook_count):
        self.menu = Menu_FoodTruck()
        self.orders = []
        self.cooks = []
        self.orders_lock = threading.Lock()
        for i in range(cook_count):
            cook = Cook(f'Cook {i+1}', self)
            self.cooks.append(cook)

    def add_order(self, order):
        with self.orders_lock:  
            self.orders.append(order)

    def get_next_order(self):
        self.orders_lock.acquire()
        if len(self.orders) > 0:
            order = self.orders.pop(0)
            self.orders_lock.release()
            return order
        self.orders_lock.release()
        return None

    def start(self):
        for cook in self.cooks:
            cook.start()

        for cook in self.cooks:
            cook.join()

# Bathroom:

class BathroomStall(threading.Thread):
    def __init__(self, name, gender, bathroom):
        super().__init__(name=name)
        self.bathroom = bathroom
        self.gender = gender

    def run(self):
        try:
            while festival.festival_running:
                person = self.bathroom.get_next_person(self.gender)
                if person is None:
                    continue
                print(f"Bathroom stall {self.name} for {self.gender} is being used by {person.id}")
                time.sleep(random.uniform(2, 5))  # Simulating bathroom time
                print(f"{person.id} has left the bathroom {self.name}")
        except Exception as e:
            print(e)

class Bathroom:
    def __init__(self, stalls_per_gender):
        self.persons = {'Male': [], 'Female': []}
        self.persons_lock = {'Male': threading.Lock(), 'Female': threading.Lock()} # one lock for each gender bathroom
        self.stalls = {'Male': [], 'Female': []}

        for gender in ['Male', 'Female']:
            for i in range(stalls_per_gender):
                stall = BathroomStall(f'B{i+1}',gender, self)
                self.stalls[gender].append(stall)

    def request_use(self, person):
        gender = person.gender
        self.persons_lock[gender].acquire()
        self.persons[gender].append(person)
        self.persons_lock[gender].release()

    def get_next_person(self, gender):
        self.persons_lock[gender].acquire()
        if len(self.persons[gender]) > 0:
            person = self.persons[gender].pop(0)
            self.persons_lock[gender].release()
            return person
        self.persons_lock[gender].release()
        return None
        
    def start(self):
        for gender in ['Male', 'Female']:
            for stall in self.stalls[gender]:
                stall.start()

    def stop(self):
        for gender in ['Male', 'Female']:
            for stall in self.stalls[gender]:
                stall.join()  

# Emergency truck:

class Doctor(threading.Thread):
    def __init__(self, name, emergency_truck):
        super().__init__(name=name)
        self.emergency_truck = emergency_truck
        self.patient = None
    
    def run(self):
        try:
            while festival.festival_running:
                self.patient = self.emergency_truck.get_next_patient()
                if self.patient is None:
                    continue
                print(f"{self.name} is treating {self.patient.id}")
                time.sleep(random.uniform(0.5, 1.5))
                self.patient.receive_notification('You have been treated! You can go back to the festival but do not drink more')
        except Exception as e:
            print(traceback.format_exc())
                
class EmergencyTruck:
    def __init__(self, doctors_count):
        self.doctors = []
        self.patients = []
        self.patients_lock = threading.Lock()
        for i in range(doctors_count):
            doctor = Doctor(f'Doctor {i+1}', self)
            self.doctors.append(doctor)
        
    def admit_patient(self, patient):
            self.patients_lock.acquire()
            self.patients.append(patient)
            self.patients_lock.release()
        
    def get_next_patient(self):
            self.patients_lock.acquire()
            if len(self.patients) > 0:
                patient = self.patients.pop(0)
                self.patients_lock.release()
                return patient
            self.patients_lock.release()
            return None
        
    def start(self):
            for doctor in self.doctors:
                doctor.start()
            
            for doctor in self.doctors:
                doctor.join()
                
# Sql connection & creation of database:

class FestivalDatabase:
    def __init__(self, user, host, database='festival_db'):
       self.conn = mysql.connector.connect(
           user=user,
           host=host
           #,password = password
           # !!! make sure to add password if it is needed for your MySQL server connection !!!
       )
       self.cursor = self.conn.cursor()

       self.create_database(database)

       # switch to the created database
       self.conn.database = database

    def create_database(self, database):
       try:
           self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database};")
           print(f"Database '{database}' created or already exists.")
       except mysql.connector.Error as err:
           print(f"Error creating database: {err}")

    def create_attendees_table(self):
       query = """
       CREATE TABLE IF NOT EXISTS attendees (
           id VARCHAR(10) PRIMARY KEY,
           age INT,
           ticket_type VARCHAR(50),
           total_drinks INT,
           total_foods INT,
           total_treatments INT,
           total_bathroom_visits INT,
           total_stage_visits INT,
           gender VARCHAR(10),
           entered_at  TIME,
           exited_at TIME
       );
       """
       self.cursor.execute(query)
       self.conn.commit()
                
    def insert_attendee(self, attendee):
       query = """
       INSERT INTO attendees (id, age, ticket_type, total_drinks, total_foods, total_treatments, total_bathroom_visits, total_stage_visits, gender, entered_at, exited_at)
       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
       ON DUPLICATE KEY UPDATE
           age = VALUES(age),
           ticket_type = VALUES(ticket_type),
           total_drinks = VALUES(total_drinks),
           total_foods = VALUES(total_foods),
           total_treatments = VALUES(total_treatments),
           total_bathroom_visits = VALUES(total_bathroom_visits),
           total_stage_visits = VALUES(total_stage_visits),
           gender = VALUES(gender),
           entered_at = VALUES(entered_at),
           exited_at = VALUES(exited_at);
       """
       entered_at_str = attendee.display_entered_at.strftime("%H:%M:%S") if attendee.display_entered_at else None
       exited_at_str = attendee.display_exited_at.strftime("%H:%M:%S") if attendee.display_exited_at else None

       values = (
           attendee.id,
           attendee.age,
           attendee.ticket.type,
           attendee.total_drinks,
           attendee.total_foods,
           attendee.total_treatments,
           attendee.total_bathroom_visits,
           attendee.total_stage_visits,
           attendee.gender,
           entered_at_str,
           exited_at_str
       )
       self.cursor.execute(query, values)
       self.conn.commit()
    
    def create_orders_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS orders (
            order_id INT AUTO_INCREMENT PRIMARY KEY,
            attendee_id VARCHAR(10),
            menu_item_name VARCHAR(50),
            price DECIMAL(5,2),
            contains_alcohol BOOLEAN,
            status VARCHAR(20),
            FOREIGN KEY (attendee_id) REFERENCES attendees(id)
        );
        """
        self.cursor.execute(query)
        self.conn.commit()
    
    def clear_orders_table(self):
        """Clear the orders table."""
        truncate_query = "TRUNCATE TABLE orders;"
        self.cursor.execute(truncate_query)
        self.conn.commit()
        # start from 1 for the orders, when you run the simulation again
    
    def insert_order(self, order):
        query = """
            INSERT INTO orders (attendee_id, menu_item_name, price, contains_alcohol, status)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            attendee_id = VALUES(attendee_id),
            menu_item_name = VALUES(menu_item_name),
            price = VALUES(price),
            contains_alcohol = VALUES(contains_alcohol),
            status = VALUES(status);
            """
        values = (
                order.attendee.id,
                order.menu_item.name,
                order.menu_item.price,
                order.menu_item.contains_alcohol,
                order.status
            )
        self.cursor.execute(query, values)
        self.conn.commit()

    def close(self):
       if self.cursor:
           self.cursor.close()
       if self.conn:
           self.conn.close()

# Main simulation class:

class FestivalSimulation:
    def __init__(self, num_attendees, num_baristas, num_cooks, num_stalls, num_security, num_doctors, num_stages, artists_info,  num_bars, num_food_trucks):
        self.attendees = [Attendee(f"A{i+1}", random.randint(18, 40), 
                                   random.choice([TicketType("VIP"), TicketType("3-day pass"), TicketType("1-day pass"), TicketType("No ticket")]), 
                                   0, 0,0,0, 0,
                                   random.choice(['Male', 'Female']), 
                                   ['food', 'drinks', 'music', 'bathroom', 'emergency']) for i in range(num_attendees)]
        
        self.bars = [Bar(num_baristas) for _ in range(num_bars)]
        self.food_trucks = [FoodTruck(num_cooks) for _ in range(num_food_trucks)]
        self.bathroom = Bathroom(num_stalls)
        self.stage = Stage(num_stages, artists_info)
        self.emergency_truck = EmergencyTruck(doctors_count=num_doctors)
        self.entrance = Entrance(num_security)
        
        self.festival_running = True 
        
        # for sql connection
        self.all_orders = []
        
        self.festival_db = FestivalDatabase(
           user='root',
           host='127.0.0.1',
           #adjust to add password here too, if needed
           database='festival_db'
        )
        self.festival_db.create_attendees_table()
        self.festival_db.create_orders_table()
        
    def collect_order(self, order):
        """Collect an order instead of directly writing to the database."""
        self.all_orders.append(order)

    def store_all_orders(self):
        """Store all collected orders in the database."""
        self.festival_db.clear_orders_table()
        for order in self.all_orders:
            self.festival_db.insert_order(order)

    def start(self):        
        try: 
            for attendee in self.attendees:
                attendee.pass_check(self.entrance)
            
            entrance_thread = threading.Thread(target=self.entrance.start)
            bar_threads = [threading.Thread(target=bar.start) for bar in self.bars] # one thread for each bar
            food_truck_threads = [threading.Thread(target=truck.start) for truck in self.food_trucks]
            bathroom_thread = threading.Thread(target=self.bathroom.start)
            emergency_truck_thread = threading.Thread(target=self.emergency_truck.start)
            stage_thread = threading.Thread(target=self.stage.start_show)

            
            entrance_thread.start()
            
            # finish entrance process
            entrance_thread.join()

            # start all services
            for thread in bar_threads:
                thread.start()
            for thread in food_truck_threads:
                thread.start()
                
            bathroom_thread.start()
            emergency_truck_thread.start()
            stage_thread.start()

            with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.attendees)) as executor:
                print("\n\nWELCOME TO PUNTA CANA FESTIVAL EVERYONE! Starting festival activities...\n\n")
                for attendee in self.attendees:
                    executor.submit(attendee.do_activities, random.choice(self.bars), random.choice(self.food_trucks), self.bathroom, self.emergency_truck, self.stage)
  
            stage_thread.join()
            self.festival_running = False
            
            print("\n\nLast festival activities have ended...\n\n")

            for thread in bar_threads:
                thread.join()
            for thread in food_truck_threads:
                thread.join()
                
            emergency_truck_thread.join()
            bathroom_thread.join()

            # store the desired data in the database:
            for attendee in self.attendees:
                self.festival_db.insert_attendee(attendee)
            
            self.store_all_orders()
            self.festival_db.close()
            
        except Exception as e:
            print(traceback.format_exc())
        
if __name__ == '__main__':
    
    random.seed(0)
    
    artists_info = [
        {'name': 'Bad Bunny', 'genre': 'Reggaeton', 'set_duration': 60},
        {'name': 'Tyler the Creator', 'genre': 'Rap', 'set_duration': 60},
        {'name': 'Doja Cat', 'genre': 'Rap', 'set_duration': 60},
        {'name': 'Kendrick Lamar', 'genre': 'Rap', 'set_duration': 30},
        {'name': 'Bad Gyal', 'genre': 'Reggaeton', 'set_duration': 60},
        {'name': 'Daddy Yankee', 'genre': 'Reggaeton', 'set_duration': 40},
        {'name': 'Karol G', 'genre': 'Reggaeton', 'set_duration': 25},
        {'name': 'Saiko', 'genre': 'Reggaeton', 'set_duration': 40},
        {'name': 'Ariana Grande', 'genre': 'Pop', 'set_duration': 35},
        {'name': 'The Weeknd', 'genre': 'Rap', 'set_duration': 20},
        {'name': 'Billie Eilish', 'genre': 'Pop', 'set_duration': 60},
        {'name': 'Post Malone', 'genre': 'Rap', 'set_duration': 30},
        {'name': 'Lil Nas X', 'genre': 'Rap', 'set_duration': 30},
        {'name': 'Dua Lipa', 'genre': 'Pop', 'set_duration': 60},
        {'name': 'Ed Sheeran', 'genre': 'Pop', 'set_duration': 35},
        {'name': 'Lizzo', 'genre': 'Pop', 'set_duration': 60}
        ] # change your set list to include your favorite artists:))):):)<3
    
    festival = FestivalSimulation(num_attendees=500, num_baristas=8, num_cooks=8, num_stalls=10, num_security=20, num_doctors=5, num_stages=3, 
                                  artists_info=artists_info, num_bars = 3, num_food_trucks=3)
    
    # you can change the numbers as you like, but make sure to have enough resources for the simulation to run smoothly
    
    festival.start()