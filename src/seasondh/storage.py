from .base import stdClass
from .base import Configuration

import os
import pymysql
import pickle
import json
import datetime
import shutil

def join(v, f='/'):
    if len(v) == 0:
        return ''
    return f.join(v)

class MySQL:
    def __init__(self, **config):
        self.config = dict()
        if 'host' in config: self.config['host'] = config['host']
        if 'port' in config: self.config['port'] = int(config['port'])
        if 'user' in config: self.config['user'] = config['user']
        if 'password' in config: self.config['password'] = config['password']
        if 'database' in config: self.config['database'] = config['database']
        if 'charset' in config: self.config['charset'] = config['charset']
        self.tablename = config['table']

    def query(self, sql, fetch=True, data=None, lastrowid=False):
        coninfo = None
        coninfo = self.config
        con = pymysql.connect(**coninfo)
        if fetch: cur = con.cursor(pymysql.cursors.DictCursor)
        else: cur = con.cursor()
        rows = cur.execute(sql, data)
        if fetch: rows = cur.fetchall()
        if lastrowid: rows = cur.lastrowid
        con.commit()
        con.close()
        return rows

    def fields(self):
        tablename = self.tablename
        columns = self.query('DESC ' + tablename)

        result = stdClass()
        result.pk = []
        result.columns = []

        for col in columns:
            if col['Key'] == 'PRI':
                result.pk.append(col['Field'])
            result.columns.append(col['Field'])
        return result

    def get(self, **values):
        try:
            tablename = self.tablename
            fields = self.fields()

            w = []
            ps = []

            for key in values:
                if key not in fields.columns: continue
                w.append('`' + key + '`=%s')
                ps.append(str(values[key]))

            w = join(w, f=' AND ')

            sql = 'SELECT * FROM `' + tablename + '` WHERE ' + w
            res = self.query(sql, data=ps, fetch=True)

            if len(res) > 0:
                return res[0]

            return None
        except Exception as e:
            return None

    def count(self, **values):
        try:
            tablename = self.tablename
            fields = self.fields()

            w = []
            ps = []

            orderby = None
            if 'orderby' in values:
                orderby = values['orderby']
                del values['orderby']

            limit = None
            if 'limit' in values:
                limit = values['limit']
                del values['limit']

            where = None
            if 'where' in values:
                where = values['where']
                del values['where']

            for key in values:
                if key not in fields.columns: continue
                w.append('`' + key + '`=%s')
                ps.append(str(values[key]))

            if len(w) > 0:
                w = join(w, f=' AND ')
                if where is not None: sql = 'SELECT count(*) as cnt FROM `' + tablename + '` WHERE (' + where + ') AND ' + w
                else: sql = 'SELECT count(*) as cnt FROM `' + tablename + '` WHERE ' + w
            elif where is not None:
                sql = 'SELECT count(*) as cnt FROM `' + tablename + '` WHERE ' + where
            else:
                sql = 'SELECT count(*) as cnt FROM `' + tablename + '`'

            if orderby is not None:
                sql = sql + ' ORDER BY ' + orderby
            if limit is not None:
                sql = sql + ' LIMIT ' + limit

            res = self.query(sql, data=ps, fetch=True)            
            return res[0]['cnt']

        except Exception as e:
            return 0

    def rows(self, **values):
        try:
            tablename = self.tablename
            fields = self.fields()

            w = []
            ps = []

            orderby = None
            if 'orderby' in values:
                orderby = values['orderby']
                del values['orderby']

            limit = None
            if 'limit' in values:
                limit = values['limit']
                del values['limit']

            where = None
            if 'where' in values:
                where = values['where']
                del values['where']

            for key in values:
                if key not in fields.columns: continue
                w.append('`' + key + '`=%s')
                ps.append(str(values[key]))

            if len(w) > 0:
                w = join(w, f=' AND ')
                if where is not None: sql = 'SELECT * FROM `' + tablename + '` WHERE (' + where + ') AND ' + w
                else: sql = 'SELECT * FROM `' + tablename + '` WHERE ' + w
            elif where is not None:
                sql = 'SELECT * FROM `' + tablename + '` WHERE ' + where
            else:
                sql = 'SELECT * FROM `' + tablename + '`'

            if orderby is not None:
                sql = sql + ' ORDER BY ' + orderby
            if limit is not None:
                sql = sql + ' LIMIT ' + limit

            res = self.query(sql, data=ps, fetch=True)            
            return res

        except Exception as e:
            return None

    def insert(self, values, **fn):
        try:
            tablename = self.tablename
            fields = self.fields()

            f = []
            v = []
            ps = []

            for key in values:
                if key not in fields.columns: continue
                f.append('`' + key + '`')
                if key in fn:
                    v.append('{}("{}")'.format(fn[key], str(values[key])))
                else:
                    v.append('%s')
                    ps.append(str(values[key]))

            f = join(f, f=',')
            v = join(v, f=',')

            sql = 'INSERT INTO `' + tablename + '`(' + f + ') VALUES(' + v + ')'
            lastrowid = self.query(sql, data=ps, fetch=False, lastrowid=True)

            return True, lastrowid
        except Exception as e:
            return False, e

    def upsert(self, values, **fn):
        try:
            tablename = self.tablename
            fields = self.fields()

            f = []
            v = []
            s = []
            ps = []

            for key in values:
                if key not in fields.columns: continue
                f.append('`' + key + '`')
                if key in fn:
                    v.append('{}("{}")'.format(fn[key], str(values[key])))
                    s.append('`{}`={}("{}")'.format(key, fn[key], str(values[key])))
                else:
                    v.append('%s')
                    s.append('`' + key + '`=%s')
                    ps.append(str(values[key]))

            f = join(f, f=',')
            v = join(v, f=',')
            s = join(s, f=',')
            ps = ps + ps

            sql = 'INSERT INTO `' + tablename + '`(' + f + ') VALUES(' + v + ') ON DUPLICATE KEY UPDATE ' + s
            res = self.query(sql, data=ps, fetch=False)

            if res == 0:
                return True, "Nothing Changed"

            return True, "Success"
        except Exception as e:
            return False, e

    def update(self, values, **where):
        try:
            tablename = self.tablename
            fields = self.fields()

            _set = []
            _where = []
            _value = []

            for key in values:
                if key not in fields.columns: continue
                v = values[key]
                if type(v) == dict:
                    _format = v['format']
                    _val = v['value']
                    _set.append(f"`{key}`={_format}")
                    _value.append(str(_val))
                else:
                    _set.append(f"`{key}`=%s")
                    _value.append(str(v))

            for key in where:
                if key not in fields.columns: continue
                v = where[key]
                if type(v) == dict:
                    val = v['value']
                    if 'op' in v:
                        op = v['op']
                        _where.append(f"`{key}`{op}%s")
                    else:
                        _where.append(f"`{key}`=%s")
                    _value.append(str(val))
                else:
                    _where.append(f"`{key}`=%s")
                    _value.append(str(v))

            _set = join(_set, f=',')
            _where = join(_where, f=' AND ')

            sql = f"UPDATE `{tablename}` SET {_set} WHERE {_where}"
            res = self.query(sql, data=_value, fetch=False)

            if res == 0:
                return True, "Nothing Changed"

            return True, "Success"
        except Exception as e:
            return False, e

class FileSystem:
    def __init__(self, basepath):
        self.basepath = basepath

    def __json__(self, jsonstr):
        try:
            return json.loads(jsonstr)
        except:
            return None

    def __walkdir__(self, dirname):
        result = []
        for root, dirs, files in os.walk(dirname):
            for filename in files:
                if filename.startswith('.'): continue
                abspath = os.path.join(root, filename)
                result.append(abspath[len(self.basepath):])
        return result

    def files(self, filepath="", page=None, dump=20, recursive=False):
        try:
            abspath = self.abspath(filepath)
            if recursive == True:
                return self.__walkdir__(abspath)

            files = os.listdir(abspath)
            if page is None:
                return files
            page = (page - 1) * dump
            return files[page:page+dump]
        except:
            return []

    def count(self, filepath=""):
        try:
            abspath = self.abspath(filepath)
            return len(os.listdir(abspath))
        except:
            return 0

    def abspath(self, filepath):
        return os.path.join(self.basepath, filepath)

    def makedirs(self, path):
        try:
            filedir = os.path.dirname(path)
            os.makedirs(filedir)
        except Exception as e:
            pass

    # file write
    def write(self, filepath, data):
        self.write_text(filepath, data)

    def write_text(self, filepath, data):
        abspath = self.abspath(filepath)
        self.makedirs(abspath)
        f = open(abspath, 'w')
        f.write(data)
        f.close()

    def write_json(self, filepath, obj):
        def json_default(value):
            if isinstance(value, datetime.date): 
                return value.strftime('%Y-%m-%d %H:%M:%S')
            return value

        obj = json.dumps(obj, default=json_default)
        abspath = self.abspath(filepath)
        self.makedirs(abspath)
        f = open(abspath, 'w')
        f.write(obj)
        f.close() 

    def write_file(self, filepath, file):
        abspath = self.abspath(filepath)
        self.makedirs(abspath)
        file.save(abspath)

    def write_pickle(self, filepath, data):
        abspath = self.abspath(filepath)
        self.makedirs(abspath)
        f = open(abspath, 'wb')
        pickle.dump(data, f)
        f.close()

    # file read
    def read(self, filepath):
        return self.read_text(filepath)

    def read_text(self, filepath):
        abspath = self.abspath(filepath)
        f = open(abspath, 'r')
        data = f.read()
        f.close()
        return data

    def read_json(self, filepath):
        abspath = self.abspath(filepath)
        f = open(abspath, 'r')
        data = f.read()
        f.close()
        data = self.__json__(data)
        return data

    def read_pickle(self, filepath):
        abspath = self.abspath(filepath)
        f = open(abspath, 'rb')
        data = pickle.load(f)
        f.close()
        return data

    # remove file
    def remove(self, filepath):
        self.delete(filepath)

    def delete(self, filepath):
        abspath = self.abspath(filepath)
        try:
            shutil.rmtree(abspath)
        except Exception as e:
            print(e)
            try:
                os.remove(abspath)
            except Exception as e:
                return False
        return True