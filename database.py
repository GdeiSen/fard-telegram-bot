import sqlite3

from models import Feedback, Dialog, Question, ServiceTicket, User, Answer

class Database:
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()

    def __del__(self):
        self.conn.close()

# USERS

    async def create_users_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                role INTEGER,
                first_name TEXT,
                last_name TEXT,
                middle_name TEXT,
                language_code TEXT,
                data_processing_consent BOOLEAN,
                object TEXT,
                legal_entity INTEGER
            )
            """
        )
        self.conn.commit()


    async def insert_user(self, user: User):
        self.cursor.execute(
            """
            INSERT INTO users (id, username, role, first_name, last_name, middle_name, language_code, data_processing_consent, object, legal_entity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user.id,
                user.username,
                user.role if user.role else -1,
                user.first_name,
                user.last_name,
                user.middle_name,
                user.language_code,
                user.data_processing_consent,
                user.object,
                user.legal_entity if user.legal_entity else ""
            )
        )
        self.conn.commit()


    async def update_user(self, user: User):
            self.cursor.execute(
                """
                UPDATE users
                SET first_name = ?, role = ?, first_name = ?, last_name = ?, middle_name = ?, language_code = ?, data_processing_consent = ?, object = ?, legal_entity = ?
                WHERE id = ?
                """,
                (
                    user.first_name,
                    user.role if user.role else None,
                    user.first_name,
                    user.last_name,
                    user.middle_name,
                    user.language_code,
                    user.data_processing_consent,
                    user.object,
                    user.legal_entity if user.legal_entity else None,
                    user.id
                )
            )
            self.conn.commit()


    async def remove_user(self, user: User):
        self.cursor.execute(
            """
            DELETE FROM users WHERE id = ?
            """,
            (user.id,)
        )
        self.conn.commit()


    async def get_user(self, user_id: int) -> User | None:
        self.cursor.execute(
            """
            SELECT id, first_name, role, first_name, last_name, middle_name, language_code, data_processing_consent, object, legal_entity
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        )
        db_user = self.cursor.fetchone()
        if db_user:
            user = User(
                id=db_user[0],
                username=db_user[1],
                role=db_user[2] if db_user[2] else None
            )
            user.first_name = db_user[3]
            user.last_name = db_user[4]
            user.middle_name = db_user[5]
            user.language_code = db_user[6]
            user.data_processing_consent = db_user[7]
            user.object = db_user[8]
            user.legal_entity = db_user[9] if db_user[9] else None
            return user
        return None


# SERVICES TICKETS


    async def create_services_tickets_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                location TEXT NOT NULL,
                image TEXT,
                checked BOOLEAN,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        self.conn.commit()


    async def insert_service_ticket(self, service_ticket: ServiceTicket):
        self.cursor.execute("""
            SELECT MAX(id) FROM services_tickets
            """)
        index = self.cursor.fetchone()[0]
        if index is None:
            index = 0
        self.cursor.execute(
            """
            INSERT INTO tickets (id, user_id, description, location, image, checked)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                index + 1,
                service_ticket.user_id,
                service_ticket.description,
                service_ticket.location,
                service_ticket.image,
                service_ticket.checked
            )
        )
        self.conn.commit()


    async def update_service_ticket(self, service_ticket: ServiceTicket):
        self.cursor.execute(
            """
            UPDATE tickets
            SET description = ?, location = ?, image = ?, checked = ?
            WHERE id = ?
            """,
            (
                service_ticket.description,
                service_ticket.location,
                service_ticket.image,
                service_ticket.checked,
                service_ticket.id
            )
        )
        self.conn.commit()


    async def remove_services_ticket(self, service_ticket: ServiceTicket):
        self.cursor.execute(
            """
            DELETE FROM tickets WHERE id = ?
            """,
            (service_ticket.id,)
        )
        self.conn.commit()


    async def get_service_ticket(self, service_ticket_id: int) -> ServiceTicket | None:
        self.cursor.execute(
            """
            SELECT id, user_id, description, location, image, checked
            FROM tickets
            WHERE id = ?
            """,
            (service_ticket_id,)
        )
        db_service_ticket = self.cursor.fetchone()
        if db_service_ticket:
            service_ticket = ServiceTicket(
                id=db_service_ticket[0],
                user_id=db_service_ticket[1],
                description=db_service_ticket[2],
                location=db_service_ticket[3],
                image=db_service_ticket[4],
                checked=db_service_ticket[5]
            )
            return service_ticket
        return None


    async def get_service_tickets(self, user_id: int) -> list[ServiceTicket]:
        self.cursor.execute(
            """
            SELECT id, user_id, description, location, image, checked
            FROM tickets
            WHERE user_id = ?
            """,
            (user_id,)
        )
        db_service_tickets = self.cursor.fetchall()
        if db_service_tickets:
            service_tickets = []
            for db_service_ticket in db_service_tickets:
                service_ticket = ServiceTicket(
                    id=db_service_ticket[0],
                    user_id=db_service_ticket[1],
                    description=db_service_ticket[2],
                    location=db_service_ticket[3],
                    image=db_service_ticket[4],
                    checked=db_service_ticket[5]
                )
                service_tickets.append(service_ticket)
            return service_tickets
        return []


# ANSWERS


    async def create_answers_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                dialog_id INTEGER NOT NULL,
                sequence_id INTEGER,
                question_id INTEGER NOT NULL,
                answer TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        self.conn.commit()


    async def insert_answer(self, user: User, answer: Answer):
        self.cursor.execute(
            """
            SELECT MAX(id) FROM answers
            """
        )
        index = self.cursor.fetchone()[0]
        if index is None:
            index = 0
        self.cursor.execute(
            """
            INSERT INTO answers (id, user_id, dialog_id, sequence_id, question_id, answer, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                index + 1,
                user.id,
                answer.dialog_id,
                answer.sequence_id,
                answer.question_id,
                answer.answer,
                answer.created_at,
            )
        )
        self.conn.commit()
        return index + 1


    async def remove_answer(self, user: User, answer: Answer):
        self.cursor.execute(
            """
            DELETE FROM answers WHERE user_id = ? AND answer_id = ?
            """,
            (user.id, answer.id)
        )
        self.conn.commit()


# FEEDBACKS


    async def create_feedbacks_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS feedbacks (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        self.conn.commit()


    async def insert_feedback(self, feedback: Feedback):
        self.cursor.execute("""
            SELECT MAX(id) FROM feedbacks
            """)
        index = self.cursor.fetchone()[0]
        if index is None:
            index = 0
        self.cursor.execute(
            """
            INSERT INTO feedbacks (id, user_id, text, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                index + 1,
                feedback.user_id,
                feedback.text,
                feedback.created_at
            )
        )
        self.conn.commit()


    async def update_feedback(self, feedback: Feedback):
        self.cursor.execute(
            """
            UPDATE feedbacks
            SET text = ?
            WHERE id = ?
            """,
            (
                feedback.text,
                feedback.id
            )
        )
        self.conn.commit()


    async def get_feedback(self, feedback_id: int) -> Feedback | None:
        self.cursor.execute(
            """
            SELECT id, user_id, text, created_at
            FROM feedbacks
            WHERE id = ?
            """,
            (feedback_id,)
        )
        db_feedback = self.cursor.fetchone()
        if db_feedback:
            feedback = Feedback(
                id=db_feedback[0],
                user_id=db_feedback[1],
                text=db_feedback[2],
                created_at=db_feedback[3]
            )
            return feedback
        return None


    async def remove_feedback(self, feedback: Feedback):
        self.cursor.execute(
            """
            DELETE FROM feedbacks WHERE id = ?
            """,
            (feedback.id,)
        )
        self.conn.commit()


    async def create_tables(self):
        await self.create_users_table()
        await self.create_services_tickets_table()
        await self.create_answers_table()
        await self.create_feedbacks_table()
