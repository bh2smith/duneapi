import csv
import os
import unittest

from tests.db.pg_client import connect


class TestMockDB(unittest.TestCase):
    def test_db_connect(self):
        db_conn = connect()
        cur = db_conn.cursor()

        table = """
            CREATE TABLE student(
                id SERIAL PRIMARY KEY, 
                firstName VARCHAR(40) NOT NULL, 
                lastName VARCHAR(40) NOT NULL, 
                age INT, 
                address VARCHAR(80), 
                email VARCHAR(40)
            )
        """
        values = [
            "Ben",
            "Smith",
            37,
            "Berlin, Germany",
            "bh2smith@gmail.com",
        ]

        insert = """
            INSERT INTO student(firstname, lastname, age, address, email) 
            VALUES(%s, %s, %s, %s, %s) RETURNING *
        """.format(
            values
        )

        cur.execute(table)
        cur.execute(insert, values)
        # Its weird the way values is used twice here!

        cur.execute("SELECT * FROM student")
        x = cur.fetchall()
        self.assertEqual(1, len(x))

    def test_db_connect(self):
        db_conn = connect()
        cur = db_conn.cursor()

        with open("tests/build_schema.sql", "r", encoding="utf-8") as file:
            populate_query = file.read()

        for filename in os.listdir('tests/data'):
            with open(os.path.join('tests', filename), 'r') as dat_file:
                reader = csv.DictReader(dat_file)
                fields = reader.fieldnames
                table = filename.replace(".csv", "")
                values = [row.values() for row in reader]
                insert_query = f"INSERT INTO {table} {fields}" \
                               f"VALUES ({','.join(values[:5])});"
                print(insert_query)

        cur.execute(populate_query)
        x = cur.fetchall()
        self.assertEqual(1, len(x))


if __name__ == "__main__":
    unittest.main()
