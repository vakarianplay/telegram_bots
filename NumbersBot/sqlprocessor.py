import sqlite3
import logging

class DBObject:
    def __init__(self, db_path):
        self.db_path = db_path
        self.connect()
        
        

    def connect(self):
        try:
            self.db = sqlite3.connect(self.db_path, check_same_thread=False)
            self.dbQuery = self.db.cursor()
            logging.info(f"Connected to database: {self.db_path}")
            self.initTables()
            # dbCommands = DBCommands(self.dbQuery)   
        except sqlite3.Error as e:
            logging.info(f"Database connection error: {e}")

    def close(self):
        if self.db:
            self.db.close()
            logging.info("Database connection closed")
            
    def initTables(self):
        users_table_query = """
        CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER NOT NULL,
        username TEXT NOT NULL
        );
        """

        numbers_table_query = """
        CREATE TABLE IF NOT EXISTS numbers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT NOT NULL,
        caption TEXT,
        tg_id INTEGER NOT NULL,
        FOREIGN KEY (tg_id) REFERENCES users (tg_id)
        );
        """
        self.dbQuery.execute(users_table_query)
        self.dbQuery.execute(numbers_table_query)
        logging.info("Init table users and numbers")
        
    def addUser(self, username, tg_id):
        queryExist = f"SELECT EXISTS(SELECT 1 FROM users WHERE tg_id = '{tg_id}');"
        existResult = self.dbQuery.execute(queryExist).fetchone()[0] 
    
        if not existResult:
            insertUserQuery = f"INSERT INTO users (tg_id, username) VALUES ('{tg_id}', '{username}');"
            self.dbQuery.execute(insertUserQuery)
            self.db.commit()
            logging.info(f"User added: username={username}, tg_id={tg_id}")
        else:
            logging.info(f"User already exists: username={username}, tg_id={tg_id}")
            
    def addNumber(self, phone, caption, tg_id):
        insertPhoneQuery = f"INSERT INTO numbers (phone, caption, tg_id) VALUES ('{phone}', '{caption}', {tg_id});"
        self.dbQuery.execute(insertPhoneQuery)
        self.db.commit()
        logging.info(f"Add rec {phone}, {caption}")
        
    def getRecords(self):
        queryGet = "SELECT phone, caption FROM numbers;"
        self.dbQuery.execute(queryGet)
        rows = self.dbQuery.fetchall()
        return rows
        
        
        


    
    
        

    