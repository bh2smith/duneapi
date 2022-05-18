import unittest

from tests.db.pg_client import connect


class TestMockDB(unittest.TestCase):
    def test_db_connect(self):
        db_conn = connect()
        cur = db_conn.cursor()

        # table = """
        #     CREATE TABLE student(
        #         id SERIAL PRIMARY KEY, 
        #         firstName VARCHAR(40) NOT NULL, 
        #         lastName VARCHAR(40) NOT NULL, 
        #         age INT, 
        #         address VARCHAR(80), 
        #         email VARCHAR(40)
        #     )
        # """
        # values = [
        #     "Ben",
        #     "Smith",
        #     37,
        #     "Berlin, Germany",
        #     "bh2smith@gmail.com",
        # ]

        # insert = """
        #     INSERT INTO student(firstname, lastname, age, address, email) 
        #     VALUES(%s, %s, %s, %s, %s) RETURNING *
        # """.format(
        #     values
        # )

        # cur.execute(table)
        # cur.execute(insert, values)
        # Its weird the way values is used twice here!

        cur.execute("SELECT count(*) FROM erc20.tokens")
        x = cur.fetchall()
        self.assertEqual(x[0], 6363)


if __name__ == "__main__":
    unittest.main()
