from pyspatialite import dbapi2 as db


class PoDB(object):

    def __init__(self, db_name):
        """
        Database object responsible to manage the connection to the database and
        creating necessary tables if not available

        :param db_name: name of the database that is going to be used
        """

        self.db_name = db_name
        self.connection = db.connect(self.db_name)
        cur = self.connection.cursor()

        # query table names
        sql = """SELECT name FROM sqlite_master WHERE type='table';"""
        result = self.connection.execute(sql)
        tables = [row[0] for row in result.fetchall()]

        if "poStation" in tables:
            print 'OK: poStation already db'
        else:
            print "INFO: Creating table poStation"
            sql = """CREATE TABLE poStation (
                    uuid char(36) NOT NULL PRIMARY KEY,
                    number char(7) NOT NULL,
                    shortname varchar,
                    longname varchar,
                    km float,
                    agency varchar,
                    longitude float,
                    latitude float,
                    water varchar)"""
            cur.execute(sql)

        if "poCurrentW" in tables:
            print "OK: poCurrentW already in db"
        else:
            print "INFO: Creating Table poCurrentW"
            sql = """CREATE TABLE poCurrentW (
                    uuid char(36) NOT NULL,
                    timestamp VARCHAR,
                    value FLOAT,
                    trend INTEGER,
                    stateMnwMhw VARCHAR,
                    stateNswHsw VARCHAR)"""
            cur.execute(sql)

        if "geometry_columns" in tables:
            print 'OK: geometry_columns already in db'
        else:
            print "INFO: Creating Geometry Entry"
            sql = 'SELECT InitSpatialMetadata(1)'  # gibt es nicht in PostGIS
            cur.execute(sql)
            sql = """SELECT AddGeometryColumn('poStation', 'geom', 4326, 'POINT', 'XY')"""
            cur.execute(sql)

        self.connection.commit()

    def fetch_query(self, sql, field_values=None):
        """
        Executes sql query to the database and returns results

        :param sql: sql_query to be executed
        :param field_values: optional fields for question mark queries
        :return: result of sql query
        """
        try:
            cursor = self.connection.cursor()
            if field_values:
                cursor.execute(sql, field_values)
            else:
                cursor.execute(sql)
            result = cursor.fetchall()
            self.connection.commit()
            return result
        except db.OperationalError:
            return []

    def clean_table(self, table):
        """
        Removes content of table

        :param table: Name of table to be cleaned
        """

        sql = 'DELETE FROM %s WHERE 1=1' % table
        self.fetch_query(sql)

    def is_empty(self, table):
        """
        Checks if table is empty

        :param table: Name of table to check
        :return: true if is empty false otherwise
        """

        sql = 'SELECT * FROM %s' % table
        result = self.fetch_query(sql)
        return len(result) == 0


if __name__ == '__main__':
    # some tests
    myDb = PoDB("../po_spatialite_db/stations.sqlite")

    myDb.is_empty("poStations")

