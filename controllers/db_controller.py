import mysql.connector
from mysql.connector import Error
import numpy as np
import pandas as pd

class MySQL():
    def __init__(self, host="localhost", user="", password=""):
        self.host = host
        self.user = user
        self.password = password
        self.current_db = None

    def connect_to_db(self, host=None, user=None, password=None, db=None):
        if not host and not user and not password and not db:
            host = self.host
            user = self.user
            password = self.password
        self.db = mysql.connector.connect(
            host = host,
            user = user,
            passwd = password,
            database = db
        )
        self.cursor = self.db.cursor()
        self.current_db = db

    def close_connection(self):
        pass

    def use_db(self, db_name):
        self.cursor.execute(f"USE {db_name};")

    def show_databases(self):
        self.cursor.execute("SHOW DATABASES")
        for x in self.cursor:
            print(x)

    def show_tables(self):
        self.cursor.execute("SHOW TABLES")
        for x in self.cursor:
            print(x)

    def create_db(self):
        pass

    def drop_db(self):
        pass

    def change_db(self):
        pass

    def get_available_engines(self):
        pass

    def change_table_engine(self):
        pass
    
    def connection(self, db_name):
        pass

    def get_tables_names(self):
        pass

    def create_table(self, table_name, fields=None): # Hanlde variables (varchar(charnb)) 
        self.cursor.execute(f"CREATE TABLE {table_name} (name VARCHAR(255), address VARCHAR(255));")

    def show_table_details(self, table_name):
        self.cursor.execute(f"DESCRIBE {table_name};")
    
    def modify_table_fields(self, table_name, fields=None):#TODO: handle fields in a dict format
        self.cursor.execute(f"ALTER TABLE {table_name};")

    def set_constraint(self, table_name, field_name, constraint):
        self.cursor.execute(f"ALTER TABLE {table_name} ALTER {field_name} SET {constraint};")

    def modify_constraint(self, table_name, field_name, new_constraint): # MUST INCLUDE VAR TYPE ex: VARCHAR(30) NOT NULL <-- where NOT NULL is the constraint
        self.cursor.execute(f"ALTER TABLE {table_name} MODIFY {field_name} {new_constraint};")

    def delete_constraint(self, table_name, field_name, constraint_name): #TODO: field dict key / value
        self.cursor.execute(f"ALTER TABLE {table_name} ALTER {field_name} DROP {constraint_name};")

    def delete_table(self):
        pass

    def select(self):
        pass

    def insert_into(self, table):
        pass

    def list_var_types(self):
        pass
    
    def insert_players_from_entrants_records(self, records_to_insert):
        self.connect_to_db()
        self.use_db("NBA")

        records = []
        for dic in records_to_insert:
            new_dict = {}
            for k, v in dic.items():
                if k not in ["nickname", "experience"]:
                    continue
                else:
                    new_dict[k] = v
            records.append(new_dict)
        # Converting list of dictionnaries to list of tuples
        values = [tuple(d.values()) for d in records]
        try:
            for record in values:
                experience = record[0]
                player_name = record[1]
                insert_stmt = "INSERT IGNORE INTO dk_players (dk_player_name, experience) VALUES (%s, %s) ON DUPLICATE KEY UPDATE experience= IF(VALUES(experience) > experience, VALUES(experience), experience)"
                data = (player_name, experience)
                self.cursor.execute(insert_stmt, data)
                self.db.commit()

        except mysql.connector.Error as error:
            print(f"Failed to insert record into MySQL table {error}")
        finally:
            if (self.db.is_connected()):
                self.cursor.close()
                self.db.close()
                print("MySQL connection is closed")

    def insert_tournaments(self, df):
        self.connect_to_db()
        self.use_db("NBA")
        for index, row in df.iterrows():
            contest_id = row["contest_id"]
            tournament_date = row["tournament_date"]
            name = row["tournament"]
            style = row["style"]
            buy_in = row["buy_in"]
            if buy_in == "Free":
                buy_in = 0
            entrants = row["entrants"]
            max_entrants = row["max_entrants"]
            total_prize = row["prize"]
            crowns = row["crowns"]
            my_entries = row["my_entries"]
            multi_entry = row["multi_entry"]
            if multi_entry == "No Multi-Entry":
                multi_entry = 0
            scraped_date = row["scraped_date"]
            summary = row["summary"]
            salary_id = row["salary_id"]
            payouts = row["payouts"]
            payouts = eval(payouts) # Transform string [{elems}] into list containing a dictionnary
            for ranking, payout in payouts[0].items():
                self.connect_to_db()
                self.use_db("NBA")
                if " - " in ranking:
                    from_rank = int(ranking.split(" - ")[0])
                    to_rank = int(ranking.split(" - ")[1])
                    print(from_rank, to_rank)
                    while from_rank != to_rank:
                        # print(from_rank)
                        insert_stmt = "INSERT IGNORE INTO dk_payouts (contest_id, ranking, payout) VALUES (%s, %s, %s)"
                        data = (contest_id, from_rank, payout)
                        self.cursor.execute(insert_stmt, data)
                        self.db.commit()
                        from_rank += 1
                else:
                    insert_stmt = "INSERT IGNORE INTO dk_payouts (contest_id, ranking, payout) VALUES (%s, %s, %s)"
                    data = (contest_id, ranking, payout)
                    self.cursor.execute(insert_stmt, data)
                    self.db.commit()

                payout_id = self.cursor.lastrowid

            insert_stmt = """
            INSERT INTO dk_tournaments (
                dk_contest_id,
                tournament_date,
                name, 
                style, 
                buy_in, 
                entrants, 
                max_entrants, 
                total_prize, 
                crowns, 
                my_entries, 
                multi_entry, 
                scraped_date,
                summary,
                payouts) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            data = (contest_id, tournament_date, name, style, buy_in, entrants, max_entrants, total_prize, crowns, my_entries, multi_entry, scraped_date, summary, payout_id, salary_id)
            self.cursor.execute(insert_stmt, data)
            self.db.commit()
        if (self.db.is_connected()):
                self.cursor.close()
                self.db.close()
                print("MySQL connection is closed")
    
    def extract_players_to_csv(self, csv_path="/home/locsta/Documents/NBA/datasets/players.csv"):
        self.connect_to_db()
        self.use_db("NBA")
        select_stmt = "SELECT dk_player_name, experience FROM dk_players"
        self.cursor.execute(select_stmt)
        df = pd.DataFrame(self.cursor.fetchall())
        df.columns = ["nickname", "experience"]
        df.to_csv(csv_path, index=None)